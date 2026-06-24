"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Concern } from "@/lib/types";

export function ConcernChart({ concerns }: { concerns: Concern[] }) {
  const data = concerns.map((concern) => ({
    name: concern.theme,
    percentage: Number(concern.percentage.toFixed(1)),
  }));

  return (
    <div>
      <div className="h-72 w-full" role="img" aria-label="Horizontal bar chart of concern frequency percentages">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ left: 10, right: 28, top: 4, bottom: 4 }}>
            <CartesianGrid stroke="var(--border)" horizontal={false} />
            <XAxis
              type="number"
              domain={[0, 100]}
              tickFormatter={(value) => `${value}%`}
              stroke="var(--faint-foreground)"
              fontSize={12}
            />
            <YAxis
              dataKey="name"
              type="category"
              width={145}
              stroke="var(--faint-foreground)"
              fontSize={12}
              tickLine={false}
            />
            <Tooltip
              formatter={(value) => [`${value}%`, "Comments"]}
              contentStyle={{
                background: "var(--surface-raised)",
                border: "1px solid var(--border)",
                borderRadius: "12px",
                color: "var(--foreground)",
              }}
            />
            <Bar dataKey="percentage" fill="var(--primary)" radius={[0, 8, 8, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <table className="mt-4 w-full text-left text-sm">
        <caption className="sr-only">Concern frequencies</caption>
        <thead>
          <tr className="border-b">
            <th className="py-2 font-semibold">Concern</th>
            <th className="py-2 text-right font-semibold">Frequency</th>
          </tr>
        </thead>
        <tbody>
          {data.map((item) => (
            <tr key={item.name} className="border-b last:border-0">
              <td className="py-2">{item.name}</td>
              <td className="py-2 text-right tabular-nums">{item.percentage}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

