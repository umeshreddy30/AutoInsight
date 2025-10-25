import React, { useState, useEffect } from 'react';
import { Loader2, CheckCircle2, XCircle, Database, BarChart3, Brain, FileText } from 'lucide-react';
import { apiService } from '../services/api';

function AnalysisProgress({ analysisId, onComplete }) {
  const [status, setStatus] = useState('starting');
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');
  const [error, setError] = useState(null);

  useEffect(() => {
    startAnalysis();
  }, []);

  const startAnalysis = async () => {
    try {
      // Start the analysis
      await apiService.startAnalysis(analysisId, {
        perform_clustering: true,
        correlation_method: 'pearson',
        generate_report: true,
        report_format: 'pdf'
      });

      // Poll for status
      pollStatus();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start analysis');
      setStatus('failed');
    }
  };

  const pollStatus = async () => {
    const maxAttempts = 120; // 2 minutes max
    let attempts = 0;

    const poll = setInterval(async () => {
      try {
        const data = await apiService.getAnalysisStatus(analysisId);
        
        // Update progress based on status
        if (data.status === 'processing') {
          setStatus('processing');
          // Simulate progress
          setProgress((prev) => Math.min(prev + 5, 95));
          
          // Update current step based on what data is available
          if (!data.dataset_info) {
            setCurrentStep('Loading and validating data...');
          } else if (data.column_statistics.length === 0) {
            setCurrentStep('Analyzing columns and statistics...');
          } else if (!data.correlation) {
            setCurrentStep('Calculating correlations...');
          } else if (data.outliers.length === 0) {
            setCurrentStep('Detecting outliers...');
          } else if (data.visualizations.length === 0) {
            setCurrentStep('Generating visualizations...');
          } else if (data.llm_insights.length === 0) {
            setCurrentStep('AI generating insights...');
          } else {
            setCurrentStep('Creating final report...');
          }
        } else if (data.status === 'completed') {
          setStatus('completed');
          setProgress(100);
          setCurrentStep('Analysis complete!');
          clearInterval(poll);
          setTimeout(() => onComplete(data), 1000);
        } else if (data.status === 'failed') {
          setStatus('failed');
          setError(data.error || 'Analysis failed');
          clearInterval(poll);
        }

        attempts++;
        if (attempts >= maxAttempts) {
          clearInterval(poll);
          setStatus('failed');
          setError('Analysis timed out');
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 1000);
  };

  const steps = [
    { icon: <Database className="w-6 h-6" />, label: 'Data Loading', key: 'loading' },
    { icon: <BarChart3 className="w-6 h-6" />, label: 'Statistical Analysis', key: 'stats' },
    { icon: <Brain className="w-6 h-6" />, label: 'AI Insights', key: 'ai' },
    { icon: <FileText className="w-6 h-6" />, label: 'Report Generation', key: 'report' },
  ];

  const getStepStatus = (index) => {
    if (status === 'failed') return 'failed';
    if (status === 'completed') return 'completed';
    if (progress > index * 25) return 'completed';
    if (progress >= index * 25) return 'active';
    return 'pending';
  };

  return (
    <div className="p-12">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-indigo-100 rounded-full mb-4">
            {status === 'failed' ? (
              <XCircle className="w-10 h-10 text-red-600" />
            ) : status === 'completed' ? (
              <CheckCircle2 className="w-10 h-10 text-green-600" />
            ) : (
              <Loader2 className="w-10 h-10 text-indigo-600 animate-spin" />
            )}
          </div>
          
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            {status === 'failed' ? 'Analysis Failed' : status === 'completed' ? 'Analysis Complete!' : 'Analyzing Your Data'}
          </h2>
          
          <p className="text-gray-600 text-lg">
            {status === 'failed' ? error : currentStep || 'Initializing...'}
          </p>
        </div>

        {/* Progress Bar */}
        {status !== 'failed' && (
          <div className="mb-12">
            <div className="flex justify-between text-sm font-medium text-gray-700 mb-2">
              <span>Progress</span>
              <span>{progress}%</span>
            </div>
            <div className="w-full h-4 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-indigo-600 to-purple-600 transition-all duration-500 ease-out"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Analysis Steps */}
        <div className="space-y-6">
          {steps.map((step, index) => {
            const stepStatus = getStepStatus(index);
            return (
              <div
                key={step.key}
                className={`flex items-center space-x-4 p-4 rounded-xl transition-all ${
                  stepStatus === 'completed'
                    ? 'bg-green-50 border-2 border-green-200'
                    : stepStatus === 'active'
                    ? 'bg-indigo-50 border-2 border-indigo-300 ring-4 ring-indigo-100'
                    : stepStatus === 'failed'
                    ? 'bg-red-50 border-2 border-red-200'
                    : 'bg-gray-50 border-2 border-gray-200'
                }`}
              >
                <div
                  className={`flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center transition-all ${
                    stepStatus === 'completed'
                      ? 'bg-green-500 text-white'
                      : stepStatus === 'active'
                      ? 'bg-indigo-600 text-white'
                      : stepStatus === 'failed'
                      ? 'bg-red-500 text-white'
                      : 'bg-gray-300 text-gray-600'
                  }`}
                >
                  {stepStatus === 'completed' ? (
                    <CheckCircle2 className="w-6 h-6" />
                  ) : stepStatus === 'active' ? (
                    <Loader2 className="w-6 h-6 animate-spin" />
                  ) : stepStatus === 'failed' ? (
                    <XCircle className="w-6 h-6" />
                  ) : (
                    step.icon
                  )}
                </div>
                
                <div className="flex-1">
                  <p className={`font-semibold ${
                    stepStatus === 'completed' ? 'text-green-900' :
                    stepStatus === 'active' ? 'text-indigo-900' :
                    stepStatus === 'failed' ? 'text-red-900' :
                    'text-gray-600'
                  }`}>
                    {step.label}
                  </p>
                  <p className="text-sm text-gray-500">
                    {stepStatus === 'completed' ? 'Completed' :
                     stepStatus === 'active' ? 'In progress...' :
                     stepStatus === 'failed' ? 'Failed' :
                     'Pending'}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Info Card */}
        {status === 'processing' && (
          <div className="mt-8 p-6 bg-blue-50 border border-blue-200 rounded-xl">
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0">
                <Brain className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <p className="font-semibold text-blue-900 mb-1">AI-Powered Analysis</p>
                <p className="text-sm text-blue-700">
                  Our AI is analyzing your data to generate professional insights, 
                  statistical summaries, and actionable recommendations. This typically 
                  takes 30-60 seconds.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Error Details */}
        {status === 'failed' && error && (
          <div className="mt-8 p-6 bg-red-50 border border-red-200 rounded-xl">
            <p className="font-semibold text-red-900 mb-2">Error Details</p>
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default AnalysisProgress;