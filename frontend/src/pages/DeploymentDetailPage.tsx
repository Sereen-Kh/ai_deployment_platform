import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Copy,
  RotateCcw,
  Trash2,
  Download,
  ChevronDown,
  AlertCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { useToast } from "@/hooks/use-toast";
import { deploymentsAPI, analyticsAPI } from "@/services/api";
import { formatDate, formatCurrency, formatNumber } from "@/lib/utils";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface LogEntry {
  timestamp: string;
  level: "INFO" | "WARN" | "ERROR";
  message: string;
}

export function DeploymentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // State
  const [selectedLogLevel, setSelectedLogLevel] = useState<
    "all" | "info" | "warn" | "error"
  >("all");
  const [searchLogs, setSearchLogs] = useState("");
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showHistoryDrawer, setShowHistoryDrawer] = useState(false);
  const [editingConfig, setEditingConfig] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    replicas: 1,
    cpu_limit: "1000m",
    memory_limit: "2Gi",
    env_vars: {} as Record<string, string>,
  });

  // Queries
  const { data: deployment, isLoading: deploymentLoading } = useQuery({
    queryKey: ["deployment", id],
    queryFn: () => (id ? deploymentsAPI.get(id) : Promise.reject()),
    enabled: !!id,
  });

  const { data: metrics, isLoading: metricsLoading } = useQuery({
    queryKey: ["metrics", id, "24h"],
    queryFn: () =>
      id
        ? analyticsAPI.getUsage("24h", { deployment_id: id })
        : Promise.reject(),
    enabled: !!id,
  });

  const { data: metricsTimeseries, isLoading: timeseriesLoading } = useQuery({
    queryKey: ["timeseries", id, "24h"],
    queryFn: () =>
      id
        ? analyticsAPI.getUsageTimeseries("latency", "24h", {
            deployment_id: id,
          })
        : Promise.reject(),
    enabled: !!id,
  });

  // Mutations
  const stopMutation = useMutation({
    mutationFn: () => (id ? deploymentsAPI.stop(id) : Promise.reject()),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["deployment", id] });
      toast({
        title: "Deployment stopped",
        description: "Your deployment has been stopped.",
      });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to stop deployment",
        description: error.response?.data?.detail || "An error occurred",
        variant: "destructive",
      });
    },
  });

  const redeployMutation = useMutation({
    mutationFn: () => (id ? deploymentsAPI.redeploy(id) : Promise.reject()),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["deployment", id] });
      toast({
        title: "Redeployment started",
        description: "Your deployment is being redeployed.",
      });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to redeploy",
        description: error.response?.data?.detail || "An error occurred",
        variant: "destructive",
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => (id ? deploymentsAPI.delete(id) : Promise.reject()),
    onSuccess: () => {
      toast({
        title: "Deployment deleted",
        description: "Your deployment has been deleted.",
      });
      navigate("/deployments");
    },
    onError: (error: any) => {
      toast({
        title: "Failed to delete deployment",
        description: error.response?.data?.detail || "An error occurred",
        variant: "destructive",
      });
    },
  });

  const updateMutation = useMutation({
    mutationFn: () =>
      id ? deploymentsAPI.update(id, formData) : Promise.reject(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["deployment", id] });
      setEditingConfig(false);
      toast({
        title: "Configuration updated",
        description: "Your deployment configuration has been saved.",
      });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to update configuration",
        description: error.response?.data?.detail || "An error occurred",
        variant: "destructive",
      });
    },
  });

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case "running":
        return "success";
      case "stopped":
        return "secondary";
      case "failed":
        return "destructive";
      case "deploying":
        return "warning";
      default:
        return "outline";
    }
  };

  const getStatusLabel = (status: string) => {
    return status.charAt(0).toUpperCase() + status.slice(1);
  };

  const copyEndpoint = () => {
    if (deployment?.endpoint_url) {
      navigator.clipboard.writeText(deployment.endpoint_url);
      toast({
        title: "Copied!",
        description: "Endpoint URL copied to clipboard.",
      });
    }
  };

  const isActionEnabled = (action: string) => {
    if (!deployment) return false;
    const status = deployment.status;

    switch (action) {
      case "stop":
        return status === "running";
      case "redeploy":
        return status !== "deploying";
      case "delete":
        return true;
      default:
        return false;
    }
  };

  const mockLogs: LogEntry[] = [
    {
      timestamp: new Date(Date.now() - 300000).toISOString(),
      level: "INFO",
      message: "Model loaded successfully",
    },
    {
      timestamp: new Date(Date.now() - 240000).toISOString(),
      level: "INFO",
      message: "Serving endpoint ready at http://localhost:8000",
    },
    {
      timestamp: new Date(Date.now() - 180000).toISOString(),
      level: "WARN",
      message: "High latency detected: avg response time 250ms",
    },
    {
      timestamp: new Date(Date.now() - 120000).toISOString(),
      level: "INFO",
      message: "Processed 1250 requests in the last hour",
    },
    {
      timestamp: new Date(Date.now() - 60000).toISOString(),
      level: "ERROR",
      message: "Timeout on request id=8123 (exceeded 30s limit)",
    },
  ];

  const filteredLogs = mockLogs.filter((log) => {
    const levelMatch =
      selectedLogLevel === "all" ||
      log.level.toLowerCase() === selectedLogLevel;
    const messageMatch = log.message
      .toLowerCase()
      .includes(searchLogs.toLowerCase());
    return levelMatch && messageMatch;
  });

  const mockDeploymentHistory = [
    {
      version: "2.3",
      timestamp: new Date(Date.now() - 3600000).toISOString(),
      action: "deployed",
      user: "amouna",
      reason: "Model update",
    },
    {
      version: "2.2",
      timestamp: new Date(Date.now() - 86400000).toISOString(),
      action: "rollback",
      user: "admin",
      reason: "Performance degradation",
    },
    {
      version: "2.1",
      timestamp: new Date(Date.now() - 259200000).toISOString(),
      action: "failed",
      user: "amouna",
      reason: "OOM error",
    },
  ];

  if (deploymentLoading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!deployment) {
    return (
      <div className="space-y-6">
        <Button variant="outline" onClick={() => navigate("/deployments")}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Deployments
        </Button>
        <Card>
          <CardContent className="flex items-center justify-center py-12">
            <div className="text-center">
              <AlertCircle className="mx-auto h-12 w-12 text-muted-foreground" />
              <p className="mt-2 text-lg font-semibold">
                Deployment not found
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
        {/* Back button */}
        <Button variant="outline" onClick={() => navigate("/deployments")}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Deployments
        </Button>

        {/* Header - Deployment Summary (Sticky) */}
        <div className="sticky top-0 z-40 space-y-4 bg-background/95 backdrop-blur pb-4">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-6">
            <div>
              <p className="text-sm text-muted-foreground">Deployment</p>
              <p className="text-lg font-semibold">{deployment.name}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Status</p>
              <Badge variant={getStatusBadgeVariant(deployment.status)}>
                {getStatusLabel(deployment.status)}
              </Badge>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Model</p>
              <p className="text-lg font-semibold">
                {deployment.config?.model?.model || "—"}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Env</p>
              <p className="text-lg font-semibold">
                {deployment.config?.environment_variables?.ENV || "—"}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Updated</p>
              <p className="text-sm">
                {deployment.updated_at
                  ? formatDate(new Date(deployment.updated_at))
                  : "—"}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Endpoint</p>
              <div className="flex items-center gap-2">
                <p className="truncate text-sm font-mono">
                  {deployment.endpoint_url || "—"}
                </p>
                {deployment.endpoint_url && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={copyEndpoint}
                    className="h-auto p-0"
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </div>
          </div>

          {/* Primary actions */}
          <div className="flex gap-2">
            <Button
              variant="outline"
              disabled={!isActionEnabled("stop") || stopMutation.isPending}
              onClick={() => stopMutation.mutate()}
            >
              {stopMutation.isPending && <Spinner size="sm" className="mr-2" />}
              Stop
            </Button>
            <Button
              variant="outline"
              disabled={!isActionEnabled("redeploy") || redeployMutation.isPending}
              onClick={() => redeployMutation.mutate()}
            >
              {redeployMutation.isPending ? (
                <Spinner size="sm" className="mr-2" />
              ) : (
                <RotateCcw className="mr-2 h-4 w-4" />
              )}
              Redeploy
            </Button>
            <Button
              variant="outline"
              disabled={!isActionEnabled("delete")}
              onClick={() => setShowDeleteConfirm(true)}
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Delete
            </Button>
          </div>
        </div>

        {/* Main content - 2 columns */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Left panel - Configuration & Controls */}
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                Configuration
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setEditingConfig(!editingConfig)}
                >
                  {editingConfig ? "Cancel" : "Edit"}
                </Button>
              </CardTitle>
              <CardDescription>
                {editingConfig
                  ? "Make changes and save"
                  : "Deployment configuration"}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Accordion type="single" collapsible defaultValue="model">
                {/* Model & Serving */}
                <AccordionItem value="model">
                  <AccordionTrigger>Model & Serving</AccordionTrigger>
                  <AccordionContent className="space-y-4 pt-4">
                    <div className="space-y-2">
                      <Label>Model Version</Label>
                      <Select
                        defaultValue={deployment.version?.toString() || "1"}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="1">v1.0</SelectItem>
                          <SelectItem value="2">v2.0</SelectItem>
                          <SelectItem value="3">v2.3</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Serving Type</Label>
                      <Select defaultValue="rest">
                        <SelectTrigger disabled>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="rest">REST</SelectItem>
                          <SelectItem value="grpc">gRPC</SelectItem>
                          <SelectItem value="batch">Batch</SelectItem>
                        </SelectContent>
                      </Select>
                      <p className="text-xs text-muted-foreground">
                        Serving type (Advanced)
                      </p>
                    </div>
                  </AccordionContent>
                </AccordionItem>

                {/* Compute & Runtime */}
                <AccordionItem value="compute">
                  <AccordionTrigger>Compute & Runtime</AccordionTrigger>
                  <AccordionContent className="space-y-4 pt-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>CPU Cores</Label>
                        <Input
                          type="text"
                          value={formData.cpu_limit}
                          onChange={(e) =>
                            setFormData({
                              ...formData,
                              cpu_limit: e.target.value,
                            })
                          }
                          disabled={!editingConfig}
                          placeholder="1000m"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Memory (GB)</Label>
                        <Input
                          type="text"
                          value={formData.memory_limit}
                          onChange={(e) =>
                            setFormData({
                              ...formData,
                              memory_limit: e.target.value,
                            })
                          }
                          disabled={!editingConfig}
                          placeholder="2Gi"
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label>GPU</Label>
                      <Select defaultValue="none" disabled>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="none">None</SelectItem>
                          <SelectItem value="t4">Tesla T4</SelectItem>
                          <SelectItem value="a100">A100</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Replicas</Label>
                      <Input
                        type="number"
                        value={formData.replicas}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            replicas: parseInt(e.target.value) || 1,
                          })
                        }
                        disabled={!editingConfig}
                        min="1"
                      />
                    </div>
                  </AccordionContent>
                </AccordionItem>

                {/* Environment & Secrets */}
                <AccordionItem value="env">
                  <AccordionTrigger>Environment & Secrets</AccordionTrigger>
                  <AccordionContent className="space-y-4 pt-4">
                    <div className="space-y-3">
                      {Object.entries(
                        deployment.config?.environment_variables || {}
                      )
                        .filter(([key]) => key !== "ENV")
                        .map(([key, value]) => (
                          <div key={key} className="space-y-1">
                            <Label className="text-xs">{key}</Label>
                            <Input
                              type="text"
                              value={String(value)}
                              disabled={!editingConfig}
                              onChange={(e) =>
                                setFormData({
                                  ...formData,
                                  env_vars: {
                                    ...formData.env_vars,
                                    [key]: e.target.value,
                                  },
                                })
                              }
                            />
                          </div>
                        ))}
                    </div>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>

              {editingConfig && (
                <div className="mt-6 flex gap-2">
                  <Button
                    onClick={() => updateMutation.mutate()}
                    disabled={updateMutation.isPending}
                  >
                    {updateMutation.isPending && <Spinner size="sm" className="mr-2" />}
                    Save Changes
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => setEditingConfig(false)}
                  >
                    Cancel
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Right panel - Monitoring */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Monitoring</CardTitle>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="overview" className="w-full">
                <TabsList>
                  <TabsTrigger value="overview">Overview</TabsTrigger>
                  <TabsTrigger value="metrics">Metrics</TabsTrigger>
                  <TabsTrigger value="cost">Cost</TabsTrigger>
                </TabsList>

                {/* Overview Tab */}
                <TabsContent value="overview" className="space-y-6">
                  <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
                    <Card>
                      <CardContent className="pt-4">
                        <div className="space-y-2">
                          <p className="text-sm text-muted-foreground">
                            Latency (p95)
                          </p>
                          <p className="text-2xl font-bold">
                            {metrics?.p95_latency_ms || "—"} ms
                          </p>
                        </div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="pt-4">
                        <div className="space-y-2">
                          <p className="text-sm text-muted-foreground">
                            Error Rate
                          </p>
                          <p className="text-2xl font-bold">
                            {metrics
                              ? (
                                  (metrics.failed_requests /
                                    metrics.total_requests) *
                                  100
                                ).toFixed(2)
                              : "—"}
                            %
                          </p>
                        </div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="pt-4">
                        <div className="space-y-2">
                          <p className="text-sm text-muted-foreground">
                            Throughput
                          </p>
                          <p className="text-2xl font-bold">
                            {metrics
                              ? formatNumber(
                                  Math.round(metrics.total_requests / 24)
                                )
                              : "—"}
                            /min
                          </p>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {metricsLoading ? (
                    <div className="flex justify-center py-8">
                      <Spinner />
                    </div>
                  ) : (
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">
                          Latency Trend
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        {metricsTimeseries && metricsTimeseries.length > 0 ? (
                          <ResponsiveContainer width="100%" height={300}>
                            <AreaChart data={metricsTimeseries}>
                              <CartesianGrid strokeDasharray="3 3" />
                              <XAxis dataKey="timestamp" />
                              <YAxis />
                              <Tooltip />
                              <Area
                                type="monotone"
                                dataKey="value"
                                stroke="#3b82f6"
                                fill="#3b82f6"
                                fillOpacity={0.1}
                              />
                            </AreaChart>
                          </ResponsiveContainer>
                        ) : (
                          <p className="text-center text-sm text-muted-foreground py-8">
                            No data available
                          </p>
                        )}
                      </CardContent>
                    </Card>
                  )}
                </TabsContent>

                {/* Metrics Tab */}
                <TabsContent value="metrics" className="space-y-4">
                  {timeseriesLoading ? (
                    <div className="flex justify-center py-8">
                      <Spinner />
                    </div>
                  ) : (
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">
                          Request Latency (24h)
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        {metricsTimeseries && metricsTimeseries.length > 0 ? (
                          <ResponsiveContainer width="100%" height={300}>
                            <LineChart data={metricsTimeseries}>
                              <CartesianGrid strokeDasharray="3 3" />
                              <XAxis dataKey="timestamp" />
                              <YAxis />
                              <Tooltip />
                              <Line
                                type="monotone"
                                dataKey="value"
                                stroke="#3b82f6"
                              />
                            </LineChart>
                          </ResponsiveContainer>
                        ) : (
                          <p className="text-center text-sm text-muted-foreground py-8">
                            No data available
                          </p>
                        )}
                      </CardContent>
                    </Card>
                  )}
                </TabsContent>

                {/* Cost Tab */}
                <TabsContent value="cost" className="space-y-4">
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Cost Overview</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-sm text-muted-foreground">
                            Daily Cost
                          </p>
                          <p className="text-2xl font-bold">
                            {formatCurrency(metrics?.daily_cost || 0)}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground">
                            Monthly Estimate
                          </p>
                          <p className="text-2xl font-bold">
                            {formatCurrency((metrics?.daily_cost || 0) * 30)}
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </div>

        {/* Logs & Events Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              Logs & Events
              <Button
                variant="ghost"
                size="sm"
                onClick={() =>
                  toast({
                    title: "Export",
                    description: "Logs exported successfully",
                  })
                }
              >
                <Download className="h-4 w-4" />
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Filters */}
            <div className="flex gap-2">
              <div className="flex-1">
                <Input
                  placeholder="Search logs..."
                  value={searchLogs}
                  onChange={(e) => setSearchLogs(e.target.value)}
                  className="h-9"
                />
              </div>
              <Select
                value={selectedLogLevel}
                onValueChange={(value: any) => setSelectedLogLevel(value)}
              >
                <SelectTrigger className="w-[140px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Levels</SelectItem>
                  <SelectItem value="info">Info</SelectItem>
                  <SelectItem value="warn">Warning</SelectItem>
                  <SelectItem value="error">Error</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Log entries */}
            <div className="space-y-2 max-h-[400px] overflow-y-auto">
              {filteredLogs.length > 0 ? (
                filteredLogs.map((log, idx) => (
                  <div
                    key={idx}
                    className="flex gap-3 rounded-lg border border-border p-3"
                  >
                    <Badge
                      variant={
                        log.level === "ERROR"
                          ? "destructive"
                          : log.level === "WARN"
                          ? "secondary"
                          : "outline"
                      }
                      className="shrink-0"
                    >
                      {log.level}
                    </Badge>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm">{log.message}</p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(log.timestamp).toLocaleString()}
                      </p>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-center text-sm text-muted-foreground py-4">
                  No logs found
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Deployment History Drawer */}
        <Card>
          <CardHeader>
            <CardTitle
              className="cursor-pointer flex items-center justify-between"
              onClick={() => setShowHistoryDrawer(!showHistoryDrawer)}
            >
              Deployment History
              <ChevronDown
                className={`h-4 w-4 transition-transform ${
                  showHistoryDrawer ? "rotate-180" : ""
                }`}
              />
            </CardTitle>
          </CardHeader>
          {showHistoryDrawer && (
            <CardContent>
              <div className="space-y-3">
                {mockDeploymentHistory.map((entry, idx) => (
                  <div
                    key={idx}
                    className="flex items-start justify-between border-l-2 border-border pl-4 py-2"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">{entry.version}</Badge>
                        <span className="text-sm font-medium capitalize">
                          {entry.action}
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">
                        {entry.reason}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        by {entry.user} •{" "}
                        {formatDate(new Date(entry.timestamp))}
                      </p>
                    </div>
                    {entry.action === "failed" && (
                      <Button variant="ghost" size="sm" disabled>
                        Rollback
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          )}
        </Card>

        {/* Delete confirmation dialog */}
        <Dialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Deployment</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this deployment? This action
              cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDeleteConfirm(false)}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => {
                deleteMutation.mutate();
                setShowDeleteConfirm(false);
              }}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending && <Spinner size="sm" className="mr-2" />}
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
