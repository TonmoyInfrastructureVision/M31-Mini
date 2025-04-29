declare module 'framer-motion' {
  import * as React from 'react';

  export interface MotionProps {
    initial?: any;
    animate?: any;
    exit?: any;
    variants?: any;
    transition?: any;
    whileHover?: any;
    whileTap?: any;
    whileFocus?: any;
    whileDrag?: any;
    [key: string]: any;
  }

  export type MotionComponent<P = {}> = React.ForwardRefExoticComponent<
    P & MotionProps & React.RefAttributes<Element>
  >;

  export type Variants = {
    [key: string]: any;
  };

  export const motion: {
    [key: string]: MotionComponent;
  };
} 