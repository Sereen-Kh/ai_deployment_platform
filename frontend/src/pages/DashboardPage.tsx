import { useQuery } from "@tanstack/react-query";
import {
  Rocket,
  DollarSign,
  Activity,
  TrendingUp,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { Layout } from "@/components/Layout";
import { analyticsAPI, deploymentsAPI } from "@/services/api";
import { formatCurrency, formatNumber } from "@/lib/utils";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts";

export function DashboardPage() {
  const { data: dashboardData, isLoading: dashboardLoading } = useQuery({
    queryKey: ["dashboard"],
    queryFn: analyticsAPI.getDashboard,
  });

  const { data: deployments, isLoading: deploymentsLoading } = useQuery({
    queryKey: ["deployments"],
    queryFn: deploymentsAPI.list,
  });

  const { data: usageData, isLoading: usageLoading } = useQuery({
    queryKey: ["usage", "7d"],
    queryFn: () => analyticsAPI.getUsage("7d"),
  });

  if (dashboardLoading || deploymentsLoading) {
    return (
      <Layout>
        <div className="flex h-[50vh] items-center justify-center">
          <Spinner size="lg" />
        </div>
      </Layout>
    );
  }

  const stats = [
    {
      name: "Total Deployments",
      value: dashboardData?.total_deployments || 0,
      icon: Rocket,
      change: "+12%",
      changeType: "positive" as const,
    },
    {
      name: "Active Deployments",
      value: dashboardData?.active_deployments || 0,
      icon: Activity,
      change: "+5%",
      changeType: "positive" as const,
    },
    {
      name: "Total Requests",
      value: formatNumber(dashboardData?.total_requests || 0),
      icon: TrendingUp,
      change: "+23%",
      changeType: "positive" as const,
    },
    {
      name: "Total Cost",
      value: formatCurrency(dashboardData?.total_cost || 0),
      icon: DollarSign,
      change: "-8%",
      changeType: "negative" as const,
    },
  ];

  const recentDeployments = deployments?.slice(0, 5) || [];

  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Overview of your AI deployments and usage
          </p>
        </div>

        {/* Stats grid */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {stats.map((stat) => (
            <Card key={stat.name}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {stat.name}
                </CardTitle>
                <stat.icon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
                <div className="flex items-center text-xs">
                  {stat.changeType === "positive" ? (
                    <ArrowUpRight className="h-3 w-3 text-green-500" />
                  ) : (
                    <ArrowDownRight className="h-3 w-3 text-red-500" />
                  )}
                  <span
                    className={
                      stat.changeType === "positive"
                        ? "text-green-500"
                        : "text-red-500"
                    }
                  >
                    {stat.change}
                  </span>
                  <span className="ml-1 text-muted-foreground">
                    from last week
                  </span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Charts */}
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Usage chart */}
          <Card>
            <CardHeader>
              <CardTitle>API Usage</CardTitle>
              <CardDescription>Requests over the last 7 days</CardDescription>
            </CardHeader>
            <CardContent>
              {usageLoading ? (
                <div className="flex h-[300px] items-center justify-center">
                  <Spinner />
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={usageData?.daily_usage || []}>
                    <CartesianGrid
                      strokeDasharray="3 3"
                      className="stroke-muted"
                    />
                    <XAxis
                      dataKey="date"
                      className="text-xs"
                      tickFormatter={(value) =>
                        new Date(value).toLocaleDateString("en-US", {
                          month: "short",
                          day: "numeric",
                        })
                      }
                    />
                    <YAxis className="text-xs" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "8px",
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="requests"
                      stroke="hsl(var(--primary))"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>

          {/* Cost chart */}
          <Card>
            <CardHeader>
              <CardTitle>Cost Breakdown</CardTitle>
              <CardDescription>
                Daily costs over the last 7 days
              </CardDescription>
            </CardHeader>
            <CardContent>
              {usageLoading ? (
                <div className="flex h-[300px] items-center justify-center">
                  <Spinner />
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={usageData?.daily_usage || []}>
                    <CartesianGrid
                      strokeDasharray="3 3"
                      className="stroke-muted"
                    />
                    <XAxis
                      dataKey="date"
                      className="text-xs"
                      tickFormatter={(value) =>
                        new Date(value).toLocaleDateString("en-US", {
                          month: "short",
                          day: "numeric",
                        })
                      }
                    />
                    <YAxis
                      className="text-xs"
                      tickFormatter={(value) => `$${value}`}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "8px",
                      }}
                      formatter={(value: number) => [
                        `$${value.toFixed(2)}`,
                        "Cost",
                      ]}
                    />
                    <Bar
                      dataKey="cost"
                      fill="hsl(var(--primary))"
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Recent deployments */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Deployments</CardTitle>
            <CardDescription>
              Your most recently created deployments
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentDeployments.length === 0 ? (
                <p className="text-center text-muted-foreground py-8">
                  No deployments yet. Create your first deployment to get
                  started.
                </p>
              ) : (
                recentDeployments.map((deployment: any) => (
                  <div
                    key={deployment.id}
                    className="flex items-center justify-between rounded-lg border p-4"
                  >
                    <div className="flex items-center gap-4">
                      <Rocket className="h-8 w-8 text-muted-foreground" />
                      <div>
                        <p className="font-medium">{deployment.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {deployment.model_name}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <Badge
                        variant={
                          deployment.status === "running"
                            ? "success"
                            : deployment.status === "stopped"
                            ? "secondary"
                            : deployment.status === "error"
                            ? "destructive"
                            : "outline"
                        }
                      >
                        {deployment.status}
                      </Badge>
                    </div>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
