"""
supabase_client.py — Supabase Database Integration
====================================================
WHY THIS FILE EXISTS:
We need PERSISTENT STORAGE for research history. Without this:
- Users lose all research when the app restarts
- There's no way to revisit or compare past research
- We can't track what topics have been researched before

Supabase provides:
1. Hosted PostgreSQL — reliable, scalable database
2. REST API — no need to write raw SQL in our Python code
3. Free tier — 500MB storage, unlimited API requests
4. Real-time subscriptions (future feature: live updates across tabs)

This module wraps all Supabase operations into clean Python functions
that the rest of the app can call without knowing anything about SQL.
"""

from datetime import datetime, timezone
import os

def get_user_supabase(token: str):
    """
    Creates a new Supabase client instance authenticated as the user.
    We must create a new instance per request to avoid race conditions
    where one user's token overwrites another's globally.
    """
    from supabase import create_client, ClientOptions
    import httpx
    
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_KEY')
    
    client = create_client(url, key, options=ClientOptions(postgrest_client_timeout=10))
    # Patch for IPv4
    ipv4_transport = httpx.HTTPTransport(local_address="0.0.0.0")
    client.postgrest.session = httpx.Client(
        base_url=f"{url}/rest/v1",
        headers=client.postgrest.session.headers,
        transport=ipv4_transport,
    )
    # Authenticate this client instance
    client.postgrest.auth(token)
    return client


def log_research_task(query, user_id, token):
    """
    Creates a new research task record in Supabase.

    Called at the START of a research pipeline. Creates a row with
    status='in_progress' so the frontend can show it immediately.

    Args:
        query: The user's research question
        user_id: The authenticated user's ID
        token: The user's JWT string

    Returns:
        The created record (dict) including its UUID

    WHY we return the full record:
    The caller needs the generated UUID to update this record later
    when each agent completes its work.
    """
    supabase = get_user_supabase(token)

    data = {
        "query": query,
        "user_id": user_id,
        "status": "in_progress",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    result = supabase.table("research_tasks").insert(data).execute()
    return result.data[0] if result.data else None


def update_research_task(task_id, updates, token):
    """
    Updates an existing research task with new data.

    Called MULTIPLE TIMES during the pipeline:
    1. After Planner: updates sub_tasks field
    2. After Search: updates sources field
    3. After Analyzer: updates analysis field
    4. After Writer: updates report field and status='completed'

    Args:
        task_id: UUID of the research task
        updates: Dict of fields to update (e.g., {"status": "completed", "report": "..."})
        token: The user's JWT string

    WHY incremental updates:
    By updating after each agent, the frontend can show partial results.
    If the pipeline fails midway, we still have whatever data was collected.
    """
    supabase = get_user_supabase(token)

    updates["updated_at"] = datetime.now(timezone.utc).isoformat()

    result = (
        supabase.table("research_tasks")
        .update(updates)
        .eq("id", task_id)
        .execute()
    )
    return result.data[0] if result.data else None


def get_research_history(user_id, token, limit=20):
    """
    Fetches recent research tasks for a specific user, newest first.

    Used by the frontend's history sidebar to show past research sessions.

    Args:
        user_id: The authenticated user's ID
        token: The user's JWT string
        limit: Max number of records to return (default 20)

    WHY only select specific columns:
    The 'report' field can be very large (2000+ words). For the history
    list, we only need the query and status. The full report is loaded
    on-demand when the user clicks a specific item.
    """
    supabase = get_user_supabase(token)

    result = (
        supabase.table("research_tasks")
        .select("id, query, status, created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data


def get_research_by_id(task_id, token):
    """
    Fetches a specific research task with ALL its data.

    Called when the user clicks a history item to view the full report.

    Args:
        task_id: UUID of the research task
        token: The user's JWT string

    Returns:
        Full record including report, sources, analysis, etc.
    """
    supabase = get_user_supabase(token)

    result = (
        supabase.table("research_tasks")
        .select("*")
        .eq("id", task_id)
        .single()
        .execute()
    )
    return result.data
