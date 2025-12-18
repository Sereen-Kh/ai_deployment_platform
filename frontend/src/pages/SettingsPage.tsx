import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Copy, Eye, EyeOff, Key, Plus, Trash2 } from "lucide-react";
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { useToast } from "@/hooks/use-toast";
import { useAuthStore } from "@/stores/authStore";
import { apiKeysAPI } from "@/services/api";
import { formatDate } from "@/lib/utils";

export function SettingsPage() {
  const [isCreateKeyOpen, setIsCreateKeyOpen] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [newKeyValue, setNewKeyValue] = useState("");
  const [visibleKeys, setVisibleKeys] = useState<Record<string, boolean>>({});

  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const { data: apiKeys, isLoading } = useQuery({
    queryKey: ["apiKeys"],
    queryFn: apiKeysAPI.list,
  });

  const createKeyMutation = useMutation({
    mutationFn: apiKeysAPI.create,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["apiKeys"] });
      setNewKeyValue(data.key);
      toast({
        title: "API key created",
        description:
          "Make sure to copy your new API key now. You won't be able to see it again!",
      });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to create API key",
        description: error.response?.data?.detail || "An error occurred",
        variant: "destructive",
      });
    },
  });

  const deleteKeyMutation = useMutation({
    mutationFn: apiKeysAPI.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["apiKeys"] });
      toast({
        title: "API key deleted",
        description: "The API key has been revoked.",
      });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to delete API key",
        description: error.response?.data?.detail || "An error occurred",
        variant: "destructive",
      });
    },
  });

  const handleCreateKey = () => {
    createKeyMutation.mutate({ name: newKeyName });
  };

  const handleCloseCreateDialog = () => {
    setIsCreateKeyOpen(false);
    setNewKeyName("");
    setNewKeyValue("");
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: "Copied!",
      description: "API key copied to clipboard.",
    });
  };

  const toggleKeyVisibility = (keyId: string) => {
    setVisibleKeys((prev) => ({ ...prev, [keyId]: !prev[keyId] }));
  };

  const maskKey = (key: string) => {
    if (key.length <= 8) return key;
    return key.slice(0, 4) + "•".repeat(key.length - 8) + key.slice(-4);
  };

  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
          <p className="text-muted-foreground">
            Manage your account and API keys
          </p>
        </div>

        <Tabs defaultValue="profile" className="space-y-6">
          <TabsList>
            <TabsTrigger value="profile">Profile</TabsTrigger>
            <TabsTrigger value="api-keys">API Keys</TabsTrigger>
          </TabsList>

          <TabsContent value="profile">
            <Card>
              <CardHeader>
                <CardTitle>Profile Information</CardTitle>
                <CardDescription>
                  Your account details and preferences
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Email</Label>
                  <Input value={user?.email || ""} disabled />
                </div>
                <div className="space-y-2">
                  <Label>Role</Label>
                  <div>
                    <Badge variant="secondary" className="capitalize">
                      {user?.role || "user"}
                    </Badge>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Account Created</Label>
                  <Input
                    value={
                      user?.created_at ? formatDate(user.created_at) : "N/A"
                    }
                    disabled
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="api-keys">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>API Keys</CardTitle>
                  <CardDescription>
                    Manage API keys for programmatic access
                  </CardDescription>
                </div>
                <Dialog
                  open={isCreateKeyOpen}
                  onOpenChange={setIsCreateKeyOpen}
                >
                  <DialogTrigger asChild>
                    <Button>
                      <Plus className="mr-2 h-4 w-4" />
                      New API Key
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>
                        {newKeyValue ? "API Key Created" : "Create API Key"}
                      </DialogTitle>
                      <DialogDescription>
                        {newKeyValue
                          ? "Copy your new API key now. You won't be able to see it again!"
                          : "Give your API key a name to help identify it later."}
                      </DialogDescription>
                    </DialogHeader>
                    {newKeyValue ? (
                      <div className="space-y-4 py-4">
                        <div className="flex items-center gap-2 rounded-lg border bg-muted p-3">
                          <code className="flex-1 text-sm break-all">
                            {newKeyValue}
                          </code>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => copyToClipboard(newKeyValue)}
                          >
                            <Copy className="h-4 w-4" />
                          </Button>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          Store this key securely. It won't be shown again.
                        </p>
                      </div>
                    ) : (
                      <div className="grid gap-4 py-4">
                        <div className="space-y-2">
                          <Label htmlFor="keyName">Name</Label>
                          <Input
                            id="keyName"
                            placeholder="My API Key"
                            value={newKeyName}
                            onChange={(e) => setNewKeyName(e.target.value)}
                          />
                        </div>
                      </div>
                    )}
                    <DialogFooter>
                      {newKeyValue ? (
                        <Button onClick={handleCloseCreateDialog}>Done</Button>
                      ) : (
                        <>
                          <Button
                            variant="outline"
                            onClick={handleCloseCreateDialog}
                          >
                            Cancel
                          </Button>
                          <Button
                            onClick={handleCreateKey}
                            disabled={
                              !newKeyName || createKeyMutation.isPending
                            }
                          >
                            {createKeyMutation.isPending ? (
                              <>
                                <Spinner size="sm" className="mr-2" />
                                Creating...
                              </>
                            ) : (
                              "Create Key"
                            )}
                          </Button>
                        </>
                      )}
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <div className="flex justify-center py-8">
                    <Spinner />
                  </div>
                ) : apiKeys?.length === 0 ? (
                  <div className="flex flex-col items-center py-8 text-center">
                    <Key className="h-12 w-12 text-muted-foreground mb-4" />
                    <p className="text-muted-foreground">
                      No API keys yet. Create one to get started.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {apiKeys?.map((key: any) => (
                      <div
                        key={key.id}
                        className="flex items-center justify-between rounded-lg border p-4"
                      >
                        <div className="flex items-center gap-4">
                          <Key className="h-5 w-5 text-muted-foreground" />
                          <div>
                            <p className="font-medium">{key.name}</p>
                            <div className="flex items-center gap-2 mt-1">
                              <code className="text-xs text-muted-foreground">
                                {visibleKeys[key.id]
                                  ? key.key_preview
                                  : maskKey(key.key_preview || "••••••••")}
                              </code>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-6 w-6"
                                onClick={() => toggleKeyVisibility(key.id)}
                              >
                                {visibleKeys[key.id] ? (
                                  <EyeOff className="h-3 w-3" />
                                ) : (
                                  <Eye className="h-3 w-3" />
                                )}
                              </Button>
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <span className="text-xs text-muted-foreground">
                            Created {formatDate(key.created_at)}
                          </span>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-destructive"
                            onClick={() => deleteKeyMutation.mutate(key.id)}
                            disabled={deleteKeyMutation.isPending}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </Layout>
  );
}
