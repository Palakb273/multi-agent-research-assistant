import { useState } from 'react';
import { supabase } from '../lib/supabase';

function AuthModal({ onAuthSuccess }) {
    const [isLogin, setIsLogin] = useState(true);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            if (isLogin) {
                const { error } = await supabase.auth.signInWithPassword({
                    email,
                    password
                });
                if (error) throw error;
            } else {
                const { error } = await supabase.auth.signUp({
                    email,
                    password
                });
                if (error) throw error;
            }
            // Assuming App is listening to authStateChange, we may not even need onAuthSuccess here
            // But we can call it just in case
            if (onAuthSuccess) onAuthSuccess();
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-overlay">
            <div className="auth-modal">
                <div className="auth-header">
                    <span className="logo-icon">🔬</span>
                    <h2>ResearchAI</h2>
                    <p>{isLogin ? 'Welcome back! Log in to continue.' : 'Create an account to save your research.'}</p>
                </div>

                <form onSubmit={handleSubmit} className="auth-form">
                    {error && <div className="auth-error">{error}</div>}

                    <div className="form-group">
                        <label htmlFor="email">Email address</label>
                        <input
                            id="email"
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="you@example.com"
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="password">Password</label>
                        <input
                            id="password"
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="••••••••"
                            required
                            minLength={6}
                        />
                    </div>

                    <button type="submit" className="auth-submit-btn" disabled={loading}>
                        {loading ? 'Please wait...' : (isLogin ? 'Log In' : 'Sign Up')}
                    </button>
                </form>

                <div className="auth-footer">
                    {isLogin ? "Don't have an account? " : "Already have an account? "}
                    <button
                        className="auth-toggle-btn"
                        onClick={() => setIsLogin(!isLogin)}
                        type="button"
                    >
                        {isLogin ? 'Sign up' : 'Log in'}
                    </button>
                </div>
            </div>
        </div>
    );
}

export default AuthModal;
