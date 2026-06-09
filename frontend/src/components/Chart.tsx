import { memo, useMemo } from "react";
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#06b6d4", "#84cc16"];

interface DataPoint {
  label: string;
  value: number;
  category?: string | null;
}

interface ChartData {
  chartType: "bar" | "line" | "pie";
  title: string;
  dataPoints: DataPoint[];
  xLabel?: string | null;
  yLabel?: string | null;
}

function transformData(dataPoints: DataPoint[]) {
  const hasCategories = dataPoints.some((dp) => dp.category);
  if (!hasCategories) {
    return dataPoints.map((dp) => ({ name: dp.label, value: dp.value }));
  }
  const categories = [...new Set(dataPoints.map((dp) => dp.category))].filter(Boolean) as string[];
  const labels = [...new Set(dataPoints.map((dp) => dp.label))];
  return labels.map((label) => {
    const row: Record<string, string | number> = { name: label };
    for (const cat of categories) {
      const match = dataPoints.find((dp) => dp.label === label && dp.category === cat);
      row[cat] = match?.value ?? 0;
    }
    return row;
  });
}

function ChartInner({ data }: { data: ChartData }) {
  const chartData = useMemo(() => transformData(data.dataPoints), [data.dataPoints]);
  const hasCategories = useMemo(() => data.dataPoints.some((dp) => dp.category), [data.dataPoints]);
  const categories = useMemo(
    () => [...new Set(data.dataPoints.map((dp) => dp.category).filter(Boolean))] as string[],
    [data.dataPoints],
  );

  if (data.chartType === "pie") {
    return (
      <div className="my-3 animate-slide-up">
        <h4 className="text-sm font-semibold text-gray-700 mb-2 text-center">{data.title}</h4>
        <div style={{ width: "100%", height: 280 }}>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label={({ name, value }: { name?: string; value?: number }) => `${name ?? ""}: ${value ?? ""}`}
              >
                {chartData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    );
  }

  const ChartType = data.chartType === "bar" ? BarChart : LineChart;
  const DataShape = data.chartType === "bar" ? Bar : Line;

  return (
    <div className="my-3 animate-slide-up">
      <h4 className="text-sm font-semibold text-gray-700 mb-2 text-center">{data.title}</h4>
      <div style={{ width: "100%", height: 280 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ChartType data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="name" label={data.xLabel ? { value: data.xLabel, position: "insideBottom", offset: -5 } : undefined} tick={{ fontSize: 12 }} />
            <YAxis label={data.yLabel ? { value: data.yLabel, angle: -90, position: "insideLeft" } : undefined} tick={{ fontSize: 12 }} />
            <Tooltip />
            {hasCategories && <Legend />}
            {hasCategories
              ? categories.map((cat, i) => (
                  <DataShape key={cat} type="monotone" dataKey={cat} fill={COLORS[i % COLORS.length]} stroke={COLORS[i % COLORS.length]} />
                ))
              : <DataShape type="monotone" dataKey="value" fill="#3b82f6" stroke="#3b82f6" />}
          </ChartType>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default memo(ChartInner);
