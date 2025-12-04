'use client';

import { useEffect } from 'react';
import { AlertCircle } from 'lucide-react';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Global error:', error);
  }, [error]);

  return (
    <html>
      <body>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          padding: '20px',
          backgroundColor: '#0a0f1a',
          color: '#e2e8f0',
          fontFamily: 'system-ui, sans-serif'
        }}>
          <div style={{
            textAlign: 'center',
            maxWidth: '600px'
          }}>
            <div style={{
              width: '64px',
              height: '64px',
              margin: '0 auto 20px',
              color: '#ef4444'
            }}>
              <AlertCircle size={64} />
            </div>
            <h1 style={{
              fontSize: '2rem',
              fontWeight: 'bold',
              marginBottom: '10px'
            }}>
              Application Error
            </h1>
            <p style={{
              marginBottom: '30px',
              opacity: 0.8
            }}>
              A critical error occurred. Please refresh the page or contact support.
            </p>
            <button
              onClick={reset}
              style={{
                padding: '12px 24px',
                backgroundColor: '#00ff88',
                color: '#0a0f1a',
                border: 'none',
                borderRadius: '8px',
                fontSize: '16px',
                fontWeight: '600',
                cursor: 'pointer'
              }}
            >
              Reload Application
            </button>
          </div>
        </div>
      </body>
    </html>
  );
}

