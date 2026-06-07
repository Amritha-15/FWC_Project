import React, { useState } from 'react';
import DashboardLayout from '../../components/layout/DashboardLayout';
import JobBoard from './tabs/JobBoard';
import Applications from './tabs/Applications';
import CandidatePipeline from './tabs/CandidatePipeline';
import InterviewFeedback from './tabs/InterviewFeedback';
import HRAnalytics from './tabs/HRAnalytics';

export const HRDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState('jobs');

  const renderTab = () => {
    switch (activeTab) {
      case 'jobs':
        return <JobBoard />;
      case 'applications':
        return <Applications />;
      case 'pipeline':
        return <CandidatePipeline />;
      case 'feedback':
        return <InterviewFeedback />;
      case 'analytics':
        return <HRAnalytics />;
      default:
        return <JobBoard />;
    }
  };

  return (
    <DashboardLayout activeTab={activeTab} onTabChange={setActiveTab} title="HR Operations & Talent Screening Portal">
      {renderTab()}
    </DashboardLayout>
  );
};

export default HRDashboard;
