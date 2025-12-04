'use client';

import { useConfiguration } from '@/hooks/useAPI';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import Layout from '@/components/Layout';
import { Settings, AlertCircle, Save, RefreshCw } from 'lucide-react';
import { useState } from 'react';
import type { Configuration } from '@/types';

export default function SettingsPage() {
  const { data: config, error, isLoading } = useConfiguration();
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState<Configuration>({});

  if (isLoading) {
    return (
      <Layout>
        <div className="space-y-8">
          <Skeleton className="h-10 w-48" />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-96" />)}
          </div>
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <Card className="max-w-2xl mx-auto mt-20">
          <CardContent className="pt-6">
            <div className="text-center">
              <AlertCircle className="w-16 h-16 text-destructive mx-auto mb-4" />
              <h2 className="text-2xl font-bold mb-2">Unable to Load Settings</h2>
              <p className="text-muted-foreground mb-6">
                Could not fetch configuration from the backend API.
              </p>
              <Button onClick={() => window.location.reload()}>Retry</Button>
            </div>
          </CardContent>
        </Card>
      </Layout>
    );
  }

  const configuration = config || {};

  const handleSave = async () => {
    // TODO: Implement save functionality with API
    console.log('Saving configuration:', formData);
    setIsEditing(false);
  };

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-foreground mb-2">Configuration</h1>
            <p className="text-muted-foreground">
              Manage system settings and integrations
            </p>
          </div>
          <div className="flex gap-2">
            {isEditing ? (
              <>
                <Button variant="outline" onClick={() => setIsEditing(false)}>
                  Cancel
                </Button>
                <Button onClick={handleSave}>
                  <Save size={16} className="mr-2" />
                  Save Changes
                </Button>
              </>
            ) : (
              <Button onClick={() => {
                setIsEditing(true);
                setFormData(configuration);
              }}>
                Edit Configuration
              </Button>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* General Settings */}
          <Card>
            <CardHeader>
              <CardTitle>General Settings</CardTitle>
              <CardDescription>Basic system configuration</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-foreground block mb-2">
                    System Mode
                  </label>
                  <Badge>
                    {configuration.system_mode || 'production'}
                  </Badge>
                </div>

                <div>
                  <label className="text-sm font-medium text-foreground block mb-2">
                    Notifications
                  </label>
                  <Badge variant={configuration.notifications_enabled ? 'default' : 'outline'}>
                    {configuration.notifications_enabled ? 'Enabled' : 'Disabled'}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* SSO Configuration */}
          <Card>
            <CardHeader>
              <CardTitle>SSO Configuration</CardTitle>
              <CardDescription>Single Sign-On settings</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-foreground block mb-2">
                    SSO Status
                  </label>
                  <Badge variant={configuration.sso_enabled ? 'default' : 'outline'}>
                    {configuration.sso_enabled ? 'Enabled' : 'Disabled'}
                  </Badge>
                </div>

                {configuration.sso_enabled && (
                  <div>
                    <label className="text-sm font-medium text-foreground block mb-2">
                      SSO Provider
                    </label>
                    <Input 
                      value={configuration.sso_provider || ''} 
                      disabled={!isEditing}
                      placeholder="e.g., okta, azure_ad, google"
                    />
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Jira Integration */}
          <Card>
            <CardHeader>
              <CardTitle>Jira Integration</CardTitle>
              <CardDescription>Connect with Jira for issue tracking</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-foreground block mb-2">
                    Jira Status
                  </label>
                  <Badge variant={configuration.jira_enabled ? 'default' : 'outline'}>
                    {configuration.jira_enabled ? 'Connected' : 'Disconnected'}
                  </Badge>
                </div>

                {configuration.jira_enabled && (
                  <>
                    <div>
                      <label className="text-sm font-medium text-foreground block mb-2">
                        Jira URL
                      </label>
                      <Input 
                        value={configuration.jira_url || ''} 
                        disabled={!isEditing}
                        placeholder="https://your-domain.atlassian.net"
                      />
                    </div>

                    <div>
                      <label className="text-sm font-medium text-foreground block mb-2">
                        Auto-create Jira Issues
                      </label>
                      <Badge variant={configuration.auto_create_jira ? 'default' : 'outline'}>
                        {configuration.auto_create_jira ? 'Enabled' : 'Disabled'}
                      </Badge>
                    </div>
                  </>
                )}
              </div>
            </CardContent>
          </Card>

          {/* API Configuration */}
          <Card>
            <CardHeader>
              <CardTitle>API Configuration</CardTitle>
              <CardDescription>API endpoint settings</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-foreground block mb-2">
                    Backend API URL
                  </label>
                  <Input 
                    value={process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8088'} 
                    disabled
                    className="font-mono text-xs"
                  />
                </div>

                <Button variant="outline" size="sm" className="w-full">
                  <RefreshCw size={14} className="mr-2" />
                  Test Connection
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Raw Configuration (for debugging) */}
        {Object.keys(configuration).length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Raw Configuration</CardTitle>
              <CardDescription>Current configuration values (for debugging)</CardDescription>
            </CardHeader>
            <CardContent>
              <pre className="p-4 bg-muted rounded-lg text-xs font-mono overflow-x-auto">
                {JSON.stringify(configuration, null, 2)}
              </pre>
            </CardContent>
          </Card>
        )}
      </div>
    </Layout>
  );
}

