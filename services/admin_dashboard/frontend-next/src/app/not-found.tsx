/**
 * 404 Not Found Page
 */

import Link from 'next/link';
import { FileQuestion, Home, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <Card className="max-w-md w-full">
        <CardContent className="pt-8 pb-8">
          <div className="text-center">
            {/* Icon */}
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-muted mb-6">
              <FileQuestion className="w-10 h-10 text-muted-foreground" />
            </div>
            
            {/* Error Code */}
            <h1 className="text-6xl font-bold text-primary mb-2">404</h1>
            
            {/* Title */}
            <h2 className="text-2xl font-semibold text-foreground mb-2">
              Page Not Found
            </h2>
            
            {/* Description */}
            <p className="text-muted-foreground mb-8">
              The page you&apos;re looking for doesn&apos;t exist or has been moved.
            </p>
            
            {/* Actions */}
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Button asChild>
                <Link href="/">
                  <Home className="w-4 h-4 mr-2" />
                  Go to Dashboard
                </Link>
              </Button>
              <Button variant="outline" asChild>
                <Link href="javascript:history.back()">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Go Back
                </Link>
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

