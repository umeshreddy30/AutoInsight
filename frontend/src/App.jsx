import React, { useState } from 'react';

function App() {
  return (
    <div style={{ padding: '40px', textAlign: 'center' }}>
      <h1 style={{ fontSize: '48px', color: '#4F46E5', marginBottom: '20px' }}>
        🎉 AutoInsight
      </h1>
      <p style={{ fontSize: '24px', color: '#6B7280' }}>
        AI-Powered Data Analytics
      </p>
      <div style={{ 
        marginTop: '40px', 
        padding: '20px', 
        background: '#F3F4F6', 
        borderRadius: '8px',
        maxWidth: '600px',
        margin: '40px auto'
      }}>
        <p style={{ fontSize: '18px', color: '#374151' }}>
          ✅ Frontend is working!
        </p>
        <p style={{ fontSize: '14px', color: '#6B7280', marginTop: '10px' }}>
          Backend should be running on port 8000
        </p>
      </div>
    </div>
  );
}

export default App;