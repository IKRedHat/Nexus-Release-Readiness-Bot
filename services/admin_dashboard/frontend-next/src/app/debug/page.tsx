'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { api, endpoints } from '@/lib/api';

export default function DebugPage() {
  const [results, setResults] = useState<any[]>([]);

  const testEndpoint = async (name: string, url: string) => {
    const startTime = Date.now();
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}${url}`, {
        headers: {
          'Content-Type': 'application/json',
        },
      });
      const duration = Date.now() - startTime;
      const data = await response.json().catch(() => response.text());
      
      setResults(prev => [...prev, {
        name,
        url,
        status: response.status,
        statusText: response.statusText,
        duration: `${duration}ms`,
        success: response.ok,
        data: JSON.stringify(data, null, 2).substring(0, 200) + '...',
      }]);
    } catch (error: any) {
      const duration = Date.now() - startTime;
      setResults(prev => [...prev, {
        name,
        url,
        status: 'ERROR',
        statusText: error.message,
        duration: `${duration}ms`,
        success: false,
        data: error.toString(),
      }]);
    }
  };

  const runTests = () => {
    setResults([]);
    Object.entries(endpoints).forEach(([name, url]) => {
      testEndpoint(name, url);
    });
  };

  return (
    <div className="container mx-auto p-8">
      <Card>
        <CardHeader>
          <CardTitle>🔧 API Debug Console</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <h3 className="font-semibold">Environment:</h3>
            <div className="bg-muted p-4 rounded font-mono text-sm space-y-1">
              <div>API URL: {process.env.NEXT_PUBLIC_API_URL || 'NOT SET'}</div>
              <div>Current Origin: {typeof window !== 'undefined' ? window.location.origin : 'SSR'}</div>
              <div>Node ENV: {process.env.NODE_ENV}</div>
            </div>
          </div>

          <Button onClick={runTests}>Run API Tests</Button>

          {results.length > 0 && (
            <div className="space-y-2">
              <h3 className="font-semibold">Test Results:</h3>
              {results.map((result, i) => (
                <div 
                  key={i} 
                  className={`p-4 rounded border ${result.success ? 'bg-green-950 border-green-700' : 'bg-red-950 border-red-700'}`}
                >
                  <div className="font-mono text-xs space-y-1">
                    <div className="font-bold">{result.name}</div>
                    <div>URL: {result.url}</div>
                    <div>Status: {result.status} {result.statusText}</div>
                    <div>Duration: {result.duration}</div>
                    <details>
                      <summary className="cursor-pointer">Response Data</summary>
                      <pre className="mt-2 text-xs whitespace-pre-wrap">{result.data}</pre>
                    </details>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

