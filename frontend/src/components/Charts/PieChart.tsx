import React from 'react';
import { motion } from 'framer-motion';

interface Segment {
  value: number;
  label: string;
  color: string;
}

interface PieChartProps {
  data: Segment[];
  size?: number;
  donut?: boolean;
  donutThickness?: number;
  showLabels?: boolean;
  showPercentage?: boolean;
  animated?: boolean;
}

const PieChart = ({ 
  data,
  size = 160,
  donut = false,
  donutThickness = 30, 
  showLabels = false,
  showPercentage = false,
  animated = true
}: PieChartProps): React.ReactElement => {
  if (!data.length) return <div className="text-center py-4">No data available</div>;
  
  const radius = size / 2;
  const innerRadius = donut ? radius - donutThickness : 0;
  const cx = radius;
  const cy = radius;
  const total = data.reduce((acc, segment) => acc + segment.value, 0);
  
  let startAngle = 0;
  const segments = data.map(segment => {
    const percentage = segment.value / total;
    const angle = percentage * 360;
    const largeArc = angle > 180 ? 1 : 0;
    
    const endAngle = startAngle + angle;
    
    const startRad = startAngle * Math.PI / 180;
    const endRad = endAngle * Math.PI / 180;
    
    const x1 = cx + radius * Math.sin(startRad);
    const y1 = cy - radius * Math.cos(startRad);
    
    const x2 = cx + radius * Math.sin(endRad);
    const y2 = cy - radius * Math.cos(endRad);
    
    const pathData = [
      `M ${cx},${cy}`,
      `L ${x1},${y1}`,
      `A ${radius},${radius} 0 ${largeArc},1 ${x2},${y2}`,
      'Z'
    ].join(' ');
    
    const result = {
      ...segment,
      percentage,
      startAngle,
      endAngle,
      pathData
    };
    
    startAngle = endAngle;
    return result;
  });
  
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {segments.map((segment, i) => (
          <motion.path
            key={`segment-${i}`}
            d={segment.pathData}
            fill={segment.color}
            initial={animated ? { opacity: 0 } : undefined}
            animate={animated ? { opacity: 1 } : undefined}
            transition={{ duration: 0.4, delay: i * 0.1 }}
          />
        ))}
        
        {donut && (
          <circle
            cx={cx}
            cy={cy}
            r={innerRadius}
            fill="white"
          />
        )}
      </svg>
      
      {showLabels && (
        <div className="mt-4 grid grid-cols-2 gap-2">
          {segments.map((segment, i) => (
            <div key={`legend-${i}`} className="flex items-center text-sm">
              <div 
                className="w-3 h-3 rounded-full mr-2"
                style={{ backgroundColor: segment.color }}
              />
              <span>{segment.label}</span>
              {showPercentage && (
                <span className="text-gray-500 ml-1">
                  ({Math.round(segment.percentage * 100)}%)
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default PieChart; 