import React, { useState } from 'react';
import Layout from '../components/Layout';
import { Dashboard, SystemMonitor, Tabs, TabContent } from '../components';
import { motion } from 'framer-motion';
import { fadeIn } from '../animations';

export default function DashboardPage(): React.ReactElement {
  const [activeTab, setActiveTab] = useState<string>('dashboard');

  return (
    <Layout title="Dashboard">
      <motion.div
        initial="hidden"
        animate="visible"
        variants={{
          hidden: { opacity: 0 },
          visible: { opacity: 1 }
        }}
      >
        <motion.div variants={fadeIn} className="mb-6">
          <Tabs
            tabs={[
              { id: 'dashboard', label: 'Dashboard', icon: '📊' },
              { id: 'monitor', label: 'System Monitor', icon: '📈' },
            ]}
            defaultValue="dashboard"
            onChange={setActiveTab}
            variant="pills"
          >
            <TabContent value="dashboard">
              <Dashboard className="mt-6" />
            </TabContent>
            <TabContent value="monitor">
              <SystemMonitor className="mt-6" />
            </TabContent>
          </Tabs>
        </motion.div>
      </motion.div>
    </Layout>
  );
} 