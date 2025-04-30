import React, { ReactNode } from 'react';
import * as TabsPrimitive from '@radix-ui/react-tabs';
import clsx from 'clsx';

interface TabItem {
  id: string;
  label: string;
  icon?: ReactNode;
}

interface TabsProps {
  tabs: TabItem[];
  defaultValue?: string;
  onChange?: (value: string) => void;
  children: ReactNode;
  variant?: 'underline' | 'pills' | 'outline';
}

const Tabs = ({
  tabs,
  defaultValue,
  onChange,
  children,
  variant = 'underline',
}: TabsProps): React.ReactElement => {
  const getTabListClasses = (): string => {
    switch (variant) {
      case 'underline':
        return 'flex border-b border-slate-200 mb-4';
      case 'pills':
        return 'flex space-x-1 p-1 bg-slate-100 rounded-lg mb-4';
      case 'outline':
        return 'flex mb-4';
      default:
        return 'flex border-b border-slate-200 mb-4';
    }
  };

  const getTabTriggerClasses = (active: boolean): string => {
    switch (variant) {
      case 'underline':
        return clsx(
          'flex items-center px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors',
          active
            ? 'border-indigo-600 text-indigo-600'
            : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
        );
      case 'pills':
        return clsx(
          'flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors',
          active
            ? 'bg-white text-indigo-700 shadow-sm'
            : 'text-slate-700 hover:bg-slate-200'
        );
      case 'outline':
        return clsx(
          'flex items-center px-3 py-2 text-sm font-medium border transition-colors',
          active
            ? 'bg-indigo-50 text-indigo-700 border-indigo-300'
            : 'border-slate-300 text-slate-700 hover:bg-slate-50'
        );
      default:
        return '';
    }
  };

  return (
    <TabsPrimitive.Root
      defaultValue={defaultValue || tabs[0].id}
      onValueChange={onChange}
    >
      <TabsPrimitive.List className={getTabListClasses()}>
        {tabs.map((tab) => (
          <TabsPrimitive.Trigger
            key={tab.id}
            value={tab.id}
            className={clsx(
              tab.icon ? 'inline-flex items-center' : '',
              getTabTriggerClasses(tab.id === (defaultValue || tabs[0].id))
            )}
          >
            {tab.icon && <span className="mr-2">{tab.icon}</span>}
            {tab.label}
          </TabsPrimitive.Trigger>
        ))}
      </TabsPrimitive.List>
      {children}
    </TabsPrimitive.Root>
  );
};

interface TabContentProps {
  value: string;
  children: ReactNode;
}

const TabContent = ({ value, children }: TabContentProps): React.ReactElement => (
  <TabsPrimitive.Content value={value} className="outline-none">
    {children}
  </TabsPrimitive.Content>
);

export { Tabs, TabContent };
export type { TabItem }; 