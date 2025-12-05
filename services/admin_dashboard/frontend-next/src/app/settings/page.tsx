'use client';

import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { DataPage } from '@/components/page';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ModeToggle } from '@/components/mode/ModeToggle';
import { 
  Save, RefreshCw, Eye, EyeOff, Loader2, CheckCircle, AlertCircle,
  Settings as SettingsIcon, Key, Database, MessageSquare, GitBranch,
  Bot, Cloud, Shield, Plug
} from 'lucide-react';
import { api } from '@/lib/api';

// ============================================================================
// Types
// ============================================================================

interface ConfigItem {
  key: string;
  value: string | null;
  masked_value: string;
  is_sensitive: boolean;
  source: 'redis' | 'env' | 'default';
  env_var: string | null;
  category: string;
}

interface ConfigResponse {
  config: ConfigItem[];
  mode: string;
  count: number;
}

interface ConfigTemplate {
  name: string;
  description: string;
  fields: {
    key: string;
    label: string;
    type: 'text' | 'url' | 'password' | 'select';
    placeholder: string;
    options?: string[];
  }[];
}

interface ConfigTemplatesResponse {
  [key: string]: ConfigTemplate;
}

// Category icons mapping
const categoryIcons: Record<string, React.ElementType> = {
  jira: Database,
  github: GitBranch,
  jenkins: Cloud,
  llm: Bot,
  slack: MessageSquare,
  confluence: Plug,
  agents: SettingsIcon,
  system: Shield,
  other: Key,
};

// ============================================================================
// Components
// ============================================================================

/**
 * Configuration Value Input
 */
function ConfigValueInput({
  field,
  value,
  onChange,
  disabled,
  isSaving,
}: {
  field: { key: string; label: string; type: string; placeholder: string; options?: string[] };
  value: string;
  onChange: (value: string) => void;
  disabled: boolean;
  isSaving: boolean;
}) {
  const [showPassword, setShowPassword] = useState(false);

  if (field.type === 'select' && field.options) {
    return (
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled || isSaving}
        className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
      >
        <option value="">Select {field.label}</option>
        {field.options.map((opt) => (
          <option key={opt} value={opt}>{opt}</option>
        ))}
      </select>
    );
  }

  if (field.type === 'password') {
    return (
      <div className="relative">
        <Input
          type={showPassword ? 'text' : 'password'}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={field.placeholder}
          disabled={disabled || isSaving}
          className="pr-10 font-mono text-sm"
        />
        <button
          type="button"
          onClick={() => setShowPassword(!showPassword)}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
        >
          {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
        </button>
      </div>
    );
  }

  return (
    <Input
      type={field.type}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={field.placeholder}
      disabled={disabled || isSaving}
      className="font-mono text-sm"
    />
  );
}

/**
 * Integration Configuration Card
 */
function IntegrationCard({
  templateKey,
  template,
  currentConfig,
  onSave,
}: {
  templateKey: string;
  template: ConfigTemplate;
  currentConfig: Record<string, string>;
  onSave: (key: string, value: string) => Promise<void>;
}) {
  const [formValues, setFormValues] = useState<Record<string, string>>({});
  const [isEditing, setIsEditing] = useState(false);
  const [savingField, setSavingField] = useState<string | null>(null);
  const Icon = categoryIcons[templateKey] || Key;

  // Initialize form values from current config
  useEffect(() => {
    const initial: Record<string, string> = {};
    template.fields.forEach(field => {
      initial[field.key] = currentConfig[field.key] || '';
    });
    setFormValues(initial);
  }, [template, currentConfig]);

  const handleSaveField = async (fieldKey: string) => {
    setSavingField(fieldKey);
    try {
      await onSave(fieldKey, formValues[fieldKey]);
      toast.success('Configuration saved', {
        description: `${fieldKey} has been updated`,
      });
    } catch (error) {
      toast.error('Failed to save', {
        description: 'Please try again',
      });
    } finally {
      setSavingField(null);
    }
  };

  const handleSaveAll = async () => {
    for (const field of template.fields) {
      if (formValues[field.key] !== currentConfig[field.key]) {
        await handleSaveField(field.key);
      }
    }
    setIsEditing(false);
  };

  // Check if any field is configured
  const isConfigured = template.fields.some(f => currentConfig[f.key]);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
              <Icon className="w-5 h-5 text-primary" />
            </div>
            <div>
              <CardTitle className="text-lg">{template.name}</CardTitle>
              <CardDescription>{template.description}</CardDescription>
            </div>
          </div>
          <Badge variant={isConfigured ? 'default' : 'outline'}>
            {isConfigured ? (
              <><CheckCircle className="w-3 h-3 mr-1" /> Configured</>
            ) : (
              <><AlertCircle className="w-3 h-3 mr-1" /> Not Configured</>
            )}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {template.fields.map((field) => (
            <div key={field.key}>
              <label className="text-sm font-medium text-foreground block mb-2">
                {field.label}
                {field.type === 'password' && (
                  <Badge variant="outline" className="ml-2 text-xs">Sensitive</Badge>
                )}
              </label>
              <div className="flex gap-2">
                <div className="flex-1">
                  <ConfigValueInput
                    field={field}
                    value={formValues[field.key] || ''}
                    onChange={(value) => setFormValues(prev => ({ ...prev, [field.key]: value }))}
                    disabled={!isEditing}
                    isSaving={savingField === field.key}
                  />
                </div>
                {isEditing && formValues[field.key] !== currentConfig[field.key] && (
                  <Button
                    size="sm"
                    onClick={() => handleSaveField(field.key)}
                    disabled={savingField === field.key}
                  >
                    {savingField === field.key ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Save className="w-4 h-4" />
                    )}
                  </Button>
                )}
              </div>
            </div>
          ))}
          
          <div className="flex gap-2 pt-4 border-t border-border">
            {isEditing ? (
              <>
                <Button variant="outline" onClick={() => setIsEditing(false)}>
                  Cancel
                </Button>
                <Button onClick={handleSaveAll}>
                  <Save className="w-4 h-4 mr-2" />
                  Save All Changes
                </Button>
              </>
            ) : (
              <Button variant="outline" onClick={() => setIsEditing(true)}>
                Edit Configuration
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Raw Configuration Viewer
 */
function RawConfigViewer({ config }: { config: ConfigItem[] }) {
  const [showRaw, setShowRaw] = useState(false);

  if (config.length === 0) return null;

  // Group by category
  const grouped = config.reduce((acc, item) => {
    if (!acc[item.category]) acc[item.category] = [];
    acc[item.category].push(item);
    return acc;
  }, {} as Record<string, ConfigItem[]>);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Current Configuration</CardTitle>
            <CardDescription>All configuration values currently in effect</CardDescription>
          </div>
          <Button variant="outline" size="sm" onClick={() => setShowRaw(!showRaw)}>
            {showRaw ? <EyeOff size={14} className="mr-2" /> : <Eye size={14} className="mr-2" />}
            {showRaw ? 'Hide Values' : 'Show Values'}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {Object.entries(grouped).map(([category, items]) => {
            const Icon = categoryIcons[category] || Key;
            return (
              <div key={category}>
                <h4 className="text-sm font-semibold text-muted-foreground uppercase mb-3 flex items-center gap-2">
                  <Icon size={14} />
                  {category}
                </h4>
                <div className="space-y-2">
                  {items.map((item) => (
                    <div key={item.key} className="flex items-center justify-between py-2 px-3 bg-muted/50 rounded-lg">
                      <div className="flex items-center gap-2">
                        <code className="text-xs font-mono text-foreground">{item.key}</code>
                        {item.is_sensitive && (
                          <Badge variant="outline" className="text-xs">🔒</Badge>
                        )}
                        <Badge variant="outline" className="text-xs">{item.source}</Badge>
                      </div>
                      <code className="text-xs font-mono text-muted-foreground">
                        {showRaw && item.value ? item.value : item.masked_value}
                      </code>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * API Connection Test
 */
function APIConnectionTest() {
  const [testing, setTesting] = useState(false);
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');

  const testConnection = async () => {
    setTesting(true);
    try {
      await api.get('/health');
      setStatus('success');
      toast.success('Connection successful', {
        description: 'Backend API is reachable',
      });
    } catch (error) {
      setStatus('error');
      toast.error('Connection failed', {
        description: 'Could not reach the backend API',
      });
    } finally {
      setTesting(false);
      setTimeout(() => setStatus('idle'), 3000);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Plug className="w-5 h-5" />
          API Connection
        </CardTitle>
        <CardDescription>Test connectivity to the backend API</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-foreground block mb-2">Backend API URL</label>
            <Input 
              value={process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8088'} 
              disabled
              className="font-mono text-xs"
            />
          </div>
          <Button 
            variant="outline" 
            className="w-full"
            onClick={testConnection}
            disabled={testing}
          >
            {testing ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : status === 'success' ? (
              <CheckCircle className="w-4 h-4 mr-2 text-green-500" />
            ) : status === 'error' ? (
              <AlertCircle className="w-4 h-4 mr-2 text-red-500" />
            ) : (
              <RefreshCw className="w-4 h-4 mr-2" />
            )}
            Test Connection
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Main Page Component
// ============================================================================

export default function SettingsPage() {
  const [config, setConfig] = useState<ConfigItem[]>([]);
  const [templates, setTemplates] = useState<ConfigTemplatesResponse>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  // Fetch configuration and templates
  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [configRes, templatesRes] = await Promise.all([
        api.get<ConfigResponse>('/config'),
        api.get<ConfigTemplatesResponse>('/config/templates'),
      ]);
      setConfig(configRes.config || []);
      setTemplates(templatesRes || {});
    } catch (err: any) {
      console.error('Failed to fetch settings:', err);
      setError(err);
    } finally {
      setIsLoading(false);
    }
  };

  // Build a lookup map for current config values
  const currentConfigMap = config.reduce((acc, item) => {
    acc[item.key] = item.value || '';
    return acc;
  }, {} as Record<string, string>);

  // Save a configuration value
  const handleSaveConfig = async (key: string, value: string) => {
    await api.post('/config', { key, value });
    // Refresh config after save
    const configRes = await api.get<ConfigResponse>('/config');
    setConfig(configRes.config || []);
  };

  return (
    <DataPage
      title="Configuration"
      description="Manage system settings, integrations, and credentials"
      isLoading={isLoading}
      error={error}
      data={config}
      onRetry={fetchData}
      errorMessage="Could not fetch configuration from the backend API."
      loadingLayout="grid"
      loadingCount={6}
    >
      {() => (
        <div className="space-y-8">
          {/* System Mode Toggle */}
          <section>
            <h2 className="text-xl font-semibold mb-4">System Mode</h2>
            <ModeToggle variant="card" />
          </section>

          {/* Integration Configurations */}
          <section>
            <h2 className="text-xl font-semibold mb-4">Integrations</h2>
            {Object.keys(templates).length > 0 ? (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {Object.entries(templates).map(([key, template]) => (
                  <IntegrationCard
                    key={key}
                    templateKey={key}
                    template={template}
                    currentConfig={currentConfigMap}
                    onSave={handleSaveConfig}
                  />
                ))}
              </div>
            ) : (
              <Card>
                <CardContent className="py-8 text-center text-muted-foreground">
                  <p>Configuration templates not available in standalone mode.</p>
                  <p className="text-sm mt-2">Connect to Redis for full configuration management.</p>
                </CardContent>
              </Card>
            )}
          </section>

          {/* API Connection */}
          <section>
            <h2 className="text-xl font-semibold mb-4">System</h2>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <APIConnectionTest />
            </div>
          </section>

          {/* Raw Configuration */}
          <section>
            <h2 className="text-xl font-semibold mb-4">All Configuration</h2>
            <RawConfigViewer config={config} />
          </section>
        </div>
      )}
    </DataPage>
  );
}
