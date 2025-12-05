'use client';

import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { Power, Loader2, FlaskConical, Radio } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { api, endpoints } from '@/lib/api';

export type SystemMode = 'mock' | 'live';

interface ModeResponse {
  mode: SystemMode;
  is_mock: boolean;
  is_live: boolean;
}

interface ModeToggleProps {
  /** Show as card (full) or inline (compact) */
  variant?: 'card' | 'inline';
  /** Callback when mode changes */
  onModeChange?: (mode: SystemMode) => void;
}

/**
 * ModeToggle Component
 * 
 * Allows switching between Mock and Production (Live) modes.
 * This affects ALL agents in the Nexus system.
 * 
 * @example
 * // Full card version (for settings page)
 * <ModeToggle variant="card" />
 * 
 * @example
 * // Inline version (for dashboard header)
 * <ModeToggle variant="inline" onModeChange={(mode) => console.log(mode)} />
 */
export function ModeToggle({ variant = 'card', onModeChange }: ModeToggleProps) {
  const [mode, setMode] = useState<SystemMode>('mock');
  const [isLoading, setIsLoading] = useState(true);
  const [isSwitching, setIsSwitching] = useState(false);

  // Fetch current mode on mount
  useEffect(() => {
    fetchMode();
  }, []);

  const fetchMode = async () => {
    setIsLoading(true);
    try {
      const response = await api.get<ModeResponse>('/mode');
      setMode(response.mode);
    } catch (error) {
      console.error('Failed to fetch mode:', error);
      // Default to mock if we can't fetch
      setMode('mock');
    } finally {
      setIsLoading(false);
    }
  };

  const switchMode = async (newMode: SystemMode) => {
    if (newMode === mode) return;

    setIsSwitching(true);
    try {
      await api.post('/mode', { mode: newMode });
      setMode(newMode);
      
      toast.success(
        newMode === 'live' ? '🚀 Switched to Production Mode' : '🧪 Switched to Mock Mode',
        {
          description: newMode === 'live' 
            ? 'All agents are now using live external services' 
            : 'All agents are now using mock data',
        }
      );

      if (onModeChange) {
        onModeChange(newMode);
      }
    } catch (error: any) {
      toast.error('Failed to switch mode', {
        description: error.response?.data?.detail || 'Please try again',
      });
    } finally {
      setIsSwitching(false);
    }
  };

  // Inline variant
  if (variant === 'inline') {
    return (
      <div className="flex items-center gap-2">
        <Badge 
          variant={mode === 'live' ? 'default' : 'outline'}
          className={`cursor-pointer ${mode === 'live' ? 'bg-green-500/10 text-green-500 border-green-500/30 hover:bg-green-500/20' : 'hover:bg-muted'}`}
          onClick={() => !isSwitching && switchMode('live')}
        >
          {isSwitching && mode !== 'live' ? (
            <Loader2 className="w-3 h-3 mr-1 animate-spin" />
          ) : (
            <Radio className="w-3 h-3 mr-1" />
          )}
          Live
        </Badge>
        <Badge 
          variant={mode === 'mock' ? 'default' : 'outline'}
          className={`cursor-pointer ${mode === 'mock' ? 'bg-yellow-500/10 text-yellow-500 border-yellow-500/30 hover:bg-yellow-500/20' : 'hover:bg-muted'}`}
          onClick={() => !isSwitching && switchMode('mock')}
        >
          {isSwitching && mode !== 'mock' ? (
            <Loader2 className="w-3 h-3 mr-1 animate-spin" />
          ) : (
            <FlaskConical className="w-3 h-3 mr-1" />
          )}
          Mock
        </Badge>
      </div>
    );
  }

  // Card variant (full)
  return (
    <Card className={mode === 'live' ? 'border-green-500/30' : 'border-yellow-500/30'}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Power className={`w-5 h-5 ${mode === 'live' ? 'text-green-500' : 'text-yellow-500'}`} />
          System Mode
        </CardTitle>
        <CardDescription>
          Toggle between Mock (testing) and Live (production) modes. This affects ALL agents.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex items-center gap-2 text-muted-foreground">
            <Loader2 className="w-4 h-4 animate-spin" />
            Loading current mode...
          </div>
        ) : (
          <div className="space-y-4">
            {/* Current Mode Display */}
            <div className="flex items-center gap-3 p-4 rounded-lg bg-muted/50">
              <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                mode === 'live' ? 'bg-green-500/10' : 'bg-yellow-500/10'
              }`}>
                {mode === 'live' ? (
                  <Radio className="w-6 h-6 text-green-500" />
                ) : (
                  <FlaskConical className="w-6 h-6 text-yellow-500" />
                )}
              </div>
              <div>
                <p className="font-semibold text-lg">
                  {mode === 'live' ? 'Production Mode' : 'Mock Mode'}
                </p>
                <p className="text-sm text-muted-foreground">
                  {mode === 'live' 
                    ? 'Using real external services (Jira, GitHub, Jenkins, etc.)'
                    : 'Using mock/simulated data for testing'}
                </p>
              </div>
            </div>

            {/* Mode Switch Buttons */}
            <div className="grid grid-cols-2 gap-3">
              <Button
                variant={mode === 'mock' ? 'default' : 'outline'}
                className={mode === 'mock' ? 'bg-yellow-500 hover:bg-yellow-600' : ''}
                onClick={() => switchMode('mock')}
                disabled={isSwitching || mode === 'mock'}
              >
                {isSwitching && mode === 'live' ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <FlaskConical className="w-4 h-4 mr-2" />
                )}
                Mock Mode
              </Button>
              <Button
                variant={mode === 'live' ? 'default' : 'outline'}
                className={mode === 'live' ? 'bg-green-500 hover:bg-green-600' : ''}
                onClick={() => switchMode('live')}
                disabled={isSwitching || mode === 'live'}
              >
                {isSwitching && mode === 'mock' ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Radio className="w-4 h-4 mr-2" />
                )}
                Live Mode
              </Button>
            </div>

            {/* Warning for Live Mode */}
            {mode === 'live' && (
              <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg text-sm">
                <p className="font-medium text-amber-500">⚠️ Live Mode Active</p>
                <p className="text-muted-foreground">
                  All actions will affect real external systems. Make sure your credentials are configured correctly.
                </p>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

