'use client';

import { useEffect } from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to an error reporting service
    console.error('Application error:', error);
  }, [error]);

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <Card className="max-w-2xl w-full">
        <CardContent className="pt-6">
          <div className="text-center">
            <AlertCircle className="w-16 h-16 text-destructive mx-auto mb-4" />
            <h1 className="text-3xl font-bold text-foreground mb-2">
              Something went wrong!
            </h1>
            <p className="text-muted-foreground mb-6">
              An unexpected error occurred. Our team has been notified.
            </p>
            
            {error.digest && (
              <div className="p-4 bg-muted rounded-lg mb-6">
                <p className="text-xs text-muted-foreground font-mono">
                  Error ID: {error.digest}
                </p>
              </div>
            )}

            <div className="flex gap-4 justify-center">
              <Button onClick={() => window.location.href = '/'}>
                Go to Dashboard
              </Button>
              <Button onClick={reset} variant="outline">
                <RefreshCw size={16} className="mr-2" />
                Try Again
              </Button>
            </div>

            <details className="mt-8 text-left">
              <summary className="cursor-pointer text-sm text-muted-foreground hover:text-foreground">
                Technical Details
              </summary>
              <pre className="mt-4 p-4 bg-muted rounded-lg text-xs overflow-auto">
                {error.message}
                {error.stack}
              </pre>
            </details>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

