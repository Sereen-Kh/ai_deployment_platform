import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Plus,
  Upload,
  Search,
  Database,
  FileText,
  Trash2,
  Send,
  MessageSquare,
} from "lucide-react";
import { Layout } from "@/components/Layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { useToast } from "@/hooks/use-toast";
import { ragAPI } from "@/services/api";
import { formatDate } from "@/lib/utils";

export function RAGPage() {
  const [isCreateCollectionOpen, setIsCreateCollectionOpen] = useState(false);
  const [isUploadDocOpen, setIsUploadDocOpen] = useState(false);
  const [selectedCollection, setSelectedCollection] = useState<string>("");
  const [newCollection, setNewCollection] = useState({
    name: "",
    description: "",
  });
  const [query, setQuery] = useState("");
  const [queryResults, setQueryResults] = useState<any[]>([]);
  const [isQuerying, setIsQuerying] = useState(false);

  const queryClient = useQueryClient();
  const { toast } = useToast();

  const { data: collections, isLoading: collectionsLoading } = useQuery({
    queryKey: ["collections"],
    queryFn: ragAPI.listCollections,
  });

  const { data: documents, isLoading: documentsLoading } = useQuery({
    queryKey: ["documents", selectedCollection],
    queryFn: () =>
      selectedCollection ? ragAPI.listDocuments(selectedCollection) : null,
    enabled: !!selectedCollection,
  });

  const createCollectionMutation = useMutation({
    mutationFn: ragAPI.createCollection,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["collections"] });
      setIsCreateCollectionOpen(false);
      setNewCollection({ name: "", description: "" });
      toast({
        title: "Collection created",
        description: "Your new collection is ready for documents.",
      });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to create collection",
        description: error.response?.data?.detail || "An error occurred",
        variant: "destructive",
      });
    },
  });

  const uploadDocMutation = useMutation({
    mutationFn: ({
      collectionId,
      file,
    }: {
      collectionId: string;
      file: File;
    }) => ragAPI.uploadDocument(collectionId, file),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["documents", selectedCollection],
      });
      setIsUploadDocOpen(false);
      toast({
        title: "Document uploaded",
        description: "Your document is being processed and indexed.",
      });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to upload document",
        description: error.response?.data?.detail || "An error occurred",
        variant: "destructive",
      });
    },
  });

  const deleteDocMutation = useMutation({
    mutationFn: ragAPI.deleteDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["documents", selectedCollection],
      });
      toast({
        title: "Document deleted",
        description: "The document has been removed from the collection.",
      });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to delete document",
        description: error.response?.data?.detail || "An error occurred",
        variant: "destructive",
      });
    },
  });

  const handleQuery = async () => {
    if (!selectedCollection || !query.trim()) return;

    setIsQuerying(true);
    try {
      const results = await ragAPI.query(selectedCollection, query);
      setQueryResults(results.results || []);
    } catch (error: any) {
      toast({
        title: "Query failed",
        description: error.response?.data?.detail || "An error occurred",
        variant: "destructive",
      });
    } finally {
      setIsQuerying(false);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && selectedCollection) {
      uploadDocMutation.mutate({ collectionId: selectedCollection, file });
    }
  };

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">
              RAG Knowledge Base
            </h1>
            <p className="text-muted-foreground">
              Manage document collections for retrieval-augmented generation
            </p>
          </div>
          <Dialog
            open={isCreateCollectionOpen}
            onOpenChange={setIsCreateCollectionOpen}
          >
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                New Collection
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create Collection</DialogTitle>
                <DialogDescription>
                  Create a new document collection for your knowledge base.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="collectionName">Name</Label>
                  <Input
                    id="collectionName"
                    placeholder="My Collection"
                    value={newCollection.name}
                    onChange={(e) =>
                      setNewCollection({
                        ...newCollection,
                        name: e.target.value,
                      })
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="collectionDesc">Description</Label>
                  <Textarea
                    id="collectionDesc"
                    placeholder="A collection of documents about..."
                    value={newCollection.description}
                    onChange={(e) =>
                      setNewCollection({
                        ...newCollection,
                        description: e.target.value,
                      })
                    }
                  />
                </div>
              </div>
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setIsCreateCollectionOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  onClick={() => createCollectionMutation.mutate(newCollection)}
                  disabled={
                    !newCollection.name || createCollectionMutation.isPending
                  }
                >
                  {createCollectionMutation.isPending ? (
                    <>
                      <Spinner size="sm" className="mr-2" />
                      Creating...
                    </>
                  ) : (
                    "Create Collection"
                  )}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>

        <Tabs defaultValue="collections" className="space-y-6">
          <TabsList>
            <TabsTrigger value="collections">Collections</TabsTrigger>
            <TabsTrigger value="query">Query</TabsTrigger>
          </TabsList>

          <TabsContent value="collections" className="space-y-6">
            {/* Collection selector */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Select Collection</CardTitle>
              </CardHeader>
              <CardContent>
                {collectionsLoading ? (
                  <Spinner />
                ) : collections?.length === 0 ? (
                  <p className="text-muted-foreground">
                    No collections yet. Create your first collection to get
                    started.
                  </p>
                ) : (
                  <Select
                    value={selectedCollection}
                    onValueChange={setSelectedCollection}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select a collection" />
                    </SelectTrigger>
                    <SelectContent>
                      {collections?.map((collection: any) => (
                        <SelectItem key={collection.id} value={collection.id}>
                          {collection.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              </CardContent>
            </Card>

            {/* Documents */}
            {selectedCollection && (
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle className="text-lg">Documents</CardTitle>
                    <CardDescription>
                      Documents in this collection
                    </CardDescription>
                  </div>
                  <Dialog
                    open={isUploadDocOpen}
                    onOpenChange={setIsUploadDocOpen}
                  >
                    <DialogTrigger asChild>
                      <Button size="sm">
                        <Upload className="mr-2 h-4 w-4" />
                        Upload
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Upload Document</DialogTitle>
                        <DialogDescription>
                          Upload a document to add to the collection. Supported
                          formats: PDF, DOCX, TXT.
                        </DialogDescription>
                      </DialogHeader>
                      <div className="py-4">
                        <Input
                          type="file"
                          accept=".pdf,.docx,.txt"
                          onChange={handleFileUpload}
                          disabled={uploadDocMutation.isPending}
                        />
                      </div>
                      {uploadDocMutation.isPending && (
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <Spinner size="sm" />
                          Uploading and processing...
                        </div>
                      )}
                    </DialogContent>
                  </Dialog>
                </CardHeader>
                <CardContent>
                  {documentsLoading ? (
                    <div className="flex justify-center py-8">
                      <Spinner />
                    </div>
                  ) : documents?.length === 0 ? (
                    <div className="flex flex-col items-center py-8 text-center">
                      <FileText className="h-12 w-12 text-muted-foreground mb-4" />
                      <p className="text-muted-foreground">
                        No documents yet. Upload your first document.
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {documents?.map((doc: any) => (
                        <div
                          key={doc.id}
                          className="flex items-center justify-between rounded-lg border p-3"
                        >
                          <div className="flex items-center gap-3">
                            <FileText className="h-5 w-5 text-muted-foreground" />
                            <div>
                              <p className="font-medium">{doc.filename}</p>
                              <p className="text-xs text-muted-foreground">
                                {formatDate(doc.created_at)}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge
                              variant={
                                doc.status === "processed"
                                  ? "success"
                                  : doc.status === "processing"
                                  ? "warning"
                                  : "destructive"
                              }
                            >
                              {doc.status}
                            </Badge>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8"
                              onClick={() => deleteDocMutation.mutate(doc.id)}
                              disabled={deleteDocMutation.isPending}
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
            )}
          </TabsContent>

          <TabsContent value="query" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Query Knowledge Base</CardTitle>
                <CardDescription>
                  Search your documents using natural language
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Collection</Label>
                  <Select
                    value={selectedCollection}
                    onValueChange={setSelectedCollection}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select a collection" />
                    </SelectTrigger>
                    <SelectContent>
                      {collections?.map((collection: any) => (
                        <SelectItem key={collection.id} value={collection.id}>
                          {collection.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Query</Label>
                  <div className="flex gap-2">
                    <Textarea
                      placeholder="Ask a question about your documents..."
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      className="min-h-[100px]"
                    />
                  </div>
                </div>
                <Button
                  onClick={handleQuery}
                  disabled={!selectedCollection || !query.trim() || isQuerying}
                  className="w-full"
                >
                  {isQuerying ? (
                    <>
                      <Spinner size="sm" className="mr-2" />
                      Searching...
                    </>
                  ) : (
                    <>
                      <Search className="mr-2 h-4 w-4" />
                      Search
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>

            {/* Query Results */}
            {queryResults.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Results</CardTitle>
                  <CardDescription>
                    Found {queryResults.length} relevant passages
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {queryResults.map((result: any, index: number) => (
                      <div
                        key={index}
                        className="rounded-lg border p-4 space-y-2"
                      >
                        <div className="flex items-center justify-between">
                          <Badge variant="outline">
                            Score: {(result.score * 100).toFixed(1)}%
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {result.metadata?.source}
                          </span>
                        </div>
                        <p className="text-sm">{result.text}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </Layout>
  );
}
