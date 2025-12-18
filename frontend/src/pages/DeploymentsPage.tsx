import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Plus,
  Play,
  Square,
  Trash2,
  MoreVertical,
  Rocket,
  Settings2,
} from "lucide-react";
import { Layout } from "@/components/Layout";
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
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { useToast } from "@/hooks/use-toast";
import { deploymentsAPI } from "@/services/api";
import { formatDate } from "@/lib/utils";

const models = [
  { value: "gpt-4", label: "GPT-4" },
  { value: "gpt-4-turbo", label: "GPT-4 Turbo" },
  { value: "gpt-3.5-turbo", label: "GPT-3.5 Turbo" },
  { value: "claude-3-opus", label: "Claude 3 Opus" },
  { value: "claude-3-sonnet", label: "Claude 3 Sonnet" },
  { value: "claude-3-haiku", label: "Claude 3 Haiku" },
];

export function DeploymentsPage() {
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [newDeployment, setNewDeployment] = useState({
    name: "",
    model_name: "gpt-4",
    max_tokens: 4096,
    temperature: 0.7,
  });

  const queryClient = useQueryClient();
  const { toast } = useToast();

  const { data: deployments, isLoading } = useQuery({
    queryKey: ["deployments"],
    queryFn: deploymentsAPI.list,
  });

  const createMutation = useMutation({
    mutationFn: deploymentsAPI.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["deployments"] });
      setIsCreateDialogOpen(false);
      setNewDeployment({
        name: "",
        model_name: "gpt-4",
        max_tokens: 4096,
        temperature: 0.7,
      });
      toast({
        title: "Deployment created",
        description: "Your new deployment has been created successfully.",
      });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to create deployment",
        description: error.response?.data?.detail || "An error occurred",
        variant: "destructive",
      });
    },
  });

  const startMutation = useMutation({
    mutationFn: deploymentsAPI.start,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["deployments"] });
      toast({
        title: "Deployment started",
        description: "Your deployment is now running.",
      });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to start deployment",
        description: error.response?.data?.detail || "An error occurred",
        variant: "destructive",
      });
    },
  });

  const stopMutation = useMutation({
    mutationFn: deploymentsAPI.stop,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["deployments"] });
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

  const deleteMutation = useMutation({
    mutationFn: deploymentsAPI.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["deployments"] });
      toast({
        title: "Deployment deleted",
        description: "Your deployment has been deleted.",
      });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to delete deployment",
        description: error.response?.data?.detail || "An error occurred",
        variant: "destructive",
      });
    },
  });

  const handleCreate = () => {
    createMutation.mutate(newDeployment);
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case "running":
        return "success";
      case "stopped":
        return "secondary";
      case "error":
        return "destructive";
      case "deploying":
        return "warning";
      default:
        return "outline";
    }
  };

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Deployments</h1>
            <p className="text-muted-foreground">
              Manage your AI model deployments
            </p>
          </div>
          <Dialog
            open={isCreateDialogOpen}
            onOpenChange={setIsCreateDialogOpen}
          >
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                New Deployment
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create Deployment</DialogTitle>
                <DialogDescription>
                  Configure and deploy a new AI model endpoint.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Name</Label>
                  <Input
                    id="name"
                    placeholder="My Deployment"
                    value={newDeployment.name}
                    onChange={(e) =>
                      setNewDeployment({
                        ...newDeployment,
                        name: e.target.value,
                      })
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="model">Model</Label>
                  <Select
                    value={newDeployment.model_name}
                    onValueChange={(value) =>
                      setNewDeployment({ ...newDeployment, model_name: value })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select a model" />
                    </SelectTrigger>
                    <SelectContent>
                      {models.map((model) => (
                        <SelectItem key={model.value} value={model.value}>
                          {model.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="max_tokens">Max Tokens</Label>
                    <Input
                      id="max_tokens"
                      type="number"
                      value={newDeployment.max_tokens}
                      onChange={(e) =>
                        setNewDeployment({
                          ...newDeployment,
                          max_tokens: parseInt(e.target.value),
                        })
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="temperature">Temperature</Label>
                    <Input
                      id="temperature"
                      type="number"
                      step="0.1"
                      min="0"
                      max="2"
                      value={newDeployment.temperature}
                      onChange={(e) =>
                        setNewDeployment({
                          ...newDeployment,
                          temperature: parseFloat(e.target.value),
                        })
                      }
                    />
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setIsCreateDialogOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleCreate}
                  disabled={!newDeployment.name || createMutation.isPending}
                >
                  {createMutation.isPending ? (
                    <>
                      <Spinner size="sm" className="mr-2" />
                      Creating...
                    </>
                  ) : (
                    "Create Deployment"
                  )}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>

        {isLoading ? (
          <div className="flex h-[50vh] items-center justify-center">
            <Spinner size="lg" />
          </div>
        ) : deployments?.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Rocket className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium">No deployments yet</h3>
              <p className="text-muted-foreground text-center max-w-sm mt-2">
                Create your first deployment to start using AI models via API.
              </p>
              <Button
                className="mt-4"
                onClick={() => setIsCreateDialogOpen(true)}
              >
                <Plus className="mr-2 h-4 w-4" />
                Create Deployment
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {deployments?.map((deployment: any) => (
              <Card key={deployment.id}>
                <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
                  <div className="space-y-1">
                    <CardTitle className="text-lg">{deployment.name}</CardTitle>
                    <CardDescription>{deployment.model_name}</CardDescription>
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon" className="h-8 w-8">
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem>
                        <Settings2 className="mr-2 h-4 w-4" />
                        Configure
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        className="text-destructive"
                        onClick={() => deleteMutation.mutate(deployment.id)}
                      >
                        <Trash2 className="mr-2 h-4 w-4" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <Badge variant={getStatusBadgeVariant(deployment.status)}>
                      {deployment.status}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      {formatDate(deployment.created_at)}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <p className="text-muted-foreground">Max Tokens</p>
                      <p className="font-medium">{deployment.max_tokens}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Temperature</p>
                      <p className="font-medium">{deployment.temperature}</p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    {deployment.status === "running" ? (
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1"
                        onClick={() => stopMutation.mutate(deployment.id)}
                        disabled={stopMutation.isPending}
                      >
                        <Square className="mr-2 h-4 w-4" />
                        Stop
                      </Button>
                    ) : (
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1"
                        onClick={() => startMutation.mutate(deployment.id)}
                        disabled={
                          startMutation.isPending ||
                          deployment.status === "deploying"
                        }
                      >
                        <Play className="mr-2 h-4 w-4" />
                        Start
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
