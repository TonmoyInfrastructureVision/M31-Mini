import React from 'react';
import { motion } from 'framer-motion';

interface DataPoint {
  value: number;
  label: string;
}

interface LineChartProps {
  data: DataPoint[];
  height?: number;
  width?: number;
  lineColor?: string;
  areaColor?: string;
  showLabels?: boolean;
  showGrid?: boolean;
  animated?: boolean;
}

const LineChart = ({ 
  data,
  height = 120,
  width = 300,
  lineColor = '#4f46e5',
  areaColor = 'rgba(79, 70, 229, 0.1)',
  showLabels = false,
  showGrid = false,
  animated = true
}: LineChartProps): React.ReactElement => {
  if (!data.length) return <div className="text-center py-4">No data available</div>;
  
  const values = data.map(item => item.value);
  const max = Math.max(...values) * 1.1;
  const min = Math.min(0, ...values) * 0.9;
  const range = max - min;
  
  const points = data.map((item, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((item.value - min) / range) * height;
    return { x, y, ...item };
  });
  
  const linePath = `M ${points.map(p => `${p.x},${p.y}`).join(' L ')}`;
  
  const areaPath = `
    M ${points[0].x},${height}
    L ${points.map(p => `${p.x},${p.y}`).join(' L ')}
    L ${points[points.length - 1].x},${height}
    Z
  `;
  
  return (
    <svg width={width} height={height} className="overflow-visible">
      {showGrid && (
        <g className="grid">
          {Array.from({ length: 5 }).map((_, i) => {
            const y = height - (i / 4) * height;
            return (
              <line 
                key={`grid-h-${i}`}
                x1={0}
                y1={y}
                x2={width}
                y2={y}
                stroke="#e5e7eb"
                strokeDasharray="2,2"
              />
            );
          })}
        </g>
      )}
      
      <motion.path
        d={areaPath}
        fill={areaColor}
        initial={animated ? { opacity: 0 } : undefined}
        animate={animated ? { opacity: 1 } : undefined}
        transition={{ duration: 1 }}
      />
      
      <motion.path
        d={linePath}
        fill="none"
        stroke={lineColor}
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
        initial={animated ? { pathLength: 0 } : undefined}
        animate={animated ? { pathLength: 1 } : undefined}
        transition={{ duration: 1.5, ease: "easeInOut" }}
      />
      
      {points.map((point, i) => (
        <motion.circle
          key={`point-${i}`}
          cx={point.x}
          cy={point.y}
          r={3}
          fill="#fff"
          stroke={lineColor}
          strokeWidth={1.5}
          initial={animated ? { scale: 0 } : undefined}
          animate={animated ? { scale: 1 } : undefined}
          transition={{ delay: 1.5 + i * 0.05, duration: 0.3 }}
        />
      ))}
      
      {showLabels && (
        <g className="labels">
          {points.map((point, i) => (
            <text
              key={`label-${i}`}
              x={point.x}
              y={height + 16}
              fontSize="10"
              textAnchor="middle"
              fill="#6b7280"
            >
              {point.label}
            </text>
          ))}
        </g>
      )}
    </svg>
  );
};

export default LineChart; 