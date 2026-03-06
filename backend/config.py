"""
config.py — Centralized Configuration
======================================
WHY THIS FILE EXISTS:
Every module in the app needs access to API keys and service clients.
Instead of scattering os.getenv() calls everywhere, we load everything
ONCE here and export ready-to-use clients. If you ever need to change
the LLM model, switch search providers, or update credentials, you
only touch this single file.
"""

import os
from dotenv import load_dotenv

# Load .env file from root directory
# WHY: python-dotenv reads the .env file and injects key-value pairs into
# os.environ, so the rest of our app can access them securely without
# hardcoding secrets in source code.
load_dotenv()

# WHY these OpenAI-compatible env vars:
# CrewAI v1.9+ internally uses OpenAI for its manager LLM and various
# internal operations. Rather than fighting this, we REDIRECT those
# calls to Groq's OpenAI-compatible API endpoint. Groq supports the
# exact same API format as OpenAI, so setting these variables makes
# CrewAI think it's talking to OpenAI — but it's actually using Groq.
# This is the officially recommended approach from the CrewAI community.
#
# IMPORTANT: We set BOTH OPENAI_API_BASE and OPENAI_BASE_URL because:
# - Older openai library versions use OPENAI_API_BASE
# - Newer openai v1+ uses OPENAI_BASE_URL
groq_key = os.getenv("GROQ_API_KEY", "")
if groq_key and not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = groq_key
    os.environ["OPENAI_API_BASE"] = "https://api.groq.com/openai/v1"
    os.environ["OPENAI_BASE_URL"] = "https://api.groq.com/openai/v1"
    os.environ["OPENAI_MODEL_NAME"] = "llama-3.3-70b-versatile"

# ─── API Keys ───────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# ─── LLM Configuration ─────────────────────────────────────
# WHY ChatGroq directly (not a string):
# CrewAI's string-based LLM config (e.g., "groq/llama-3.3-70b-versatile")
# requires the `litellm` package. Instead, we use langchain-groq's ChatGroq
# directly, which is already installed and works natively with CrewAI.
# Groq's LPU inference is EXTREMELY fast — 10-30x faster than GPU-based hosting.
LLM_MODEL_NAME = "llama-3.3-70b-versatile"

_llm_instance = None

def get_llm():
    """
    Returns a singleton ChatGroq LLM instance.
    WHY lazy init: Importing and creating the LLM at module load time
    would crash if GROQ_API_KEY isn't set. Lazy init defers the crash
    to when the LLM is actually needed.
    """
    global _llm_instance
    if _llm_instance is None:
        if not GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY must be set in .env file. "
                "Get it free at https://console.groq.com"
            )
        from langchain_groq import ChatGroq
        _llm_instance = ChatGroq(
            model=LLM_MODEL_NAME,
            api_key=GROQ_API_KEY,
            temperature=0.7,
        )
    return _llm_instance

# ─── Supabase Client ───────────────────────────────────────
# WHY lazy initialization:
# We don't want to crash on import if keys aren't set yet (e.g. during
# frontend-only development). We initialize only when actually needed.
_supabase_client = None

def get_supabase_client():
    """
    Returns a singleton Supabase client.
    WHY singleton: We only need one connection to Supabase throughout
    the app's lifetime. Creating multiple clients wastes resources.

    WHY custom httpx transport with local_address='0.0.0.0':
    Python's httpx library (used by supabase-py) prefers IPv6 by default.
    On networks where IPv6 doesn't route properly (e.g. NAT64 addresses),
    this causes connections to hang/timeout indefinitely. Binding to
    '0.0.0.0' forces IPv4, which resolves the issue.
    """
    global _supabase_client
    if _supabase_client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY must be set in .env file. "
                "Get these from your Supabase project settings."
            )
        from supabase import create_client, ClientOptions
        import httpx

        # Force IPv4 to avoid IPv6 routing issues
        _supabase_client = create_client(
            SUPABASE_URL,
            SUPABASE_KEY,
            options=ClientOptions(
                postgrest_client_timeout=10,
            ),
        )
        # Patch the underlying httpx client to force IPv4
        ipv4_transport = httpx.HTTPTransport(local_address="0.0.0.0")
        _supabase_client.postgrest.session = httpx.Client(
            base_url=f"{SUPABASE_URL}/rest/v1",
            headers=_supabase_client.postgrest.session.headers,
            transport=ipv4_transport,
        )
    return _supabase_client
