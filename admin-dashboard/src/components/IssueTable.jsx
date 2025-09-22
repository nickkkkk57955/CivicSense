import React, { useState, useEffect } from 'react';
import { Table, Tag, Button, Space, Modal, Select } from 'antd';
import axios from 'axios';

const { Option } = Select;

const IssueTable = () => {
  const [issues, setIssues] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchIssues();
  }, []);

  const fetchIssues = async () => {
    setLoading(true);
    try {
      const response = await axios.get('http://localhost:8000/issues/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      setIssues(response.data);
    } catch (error) {
      console.error('Error fetching issues:', error);
    }
    setLoading(false);
  };

  const updateIssueStatus = async (issueId, newStatus) => {
    try {
      await axios.put(`http://localhost:8000/issues/${issueId}`, {
        status: newStatus
      }, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      fetchIssues(); // Refresh the list
    } catch (error) {
      console.error('Error updating issue:', error);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      'submitted': 'red',
      'acknowledged': 'orange',
      'in_progress': 'blue',
      'resolved': 'green',
      'closed': 'gray'
    };
    return colors[status] || 'default';
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60,
    },
    {
      title: 'Title',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
    },
    {
      title: 'Category',
      dataIndex: 'category',
      key: 'category',
      render: (category) => category.replace('_', ' ').toUpperCase(),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Tag color={getStatusColor(status)}>
          {status.replace('_', ' ').toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'Priority',
      dataIndex: 'priority',
      key: 'priority',
      render: (priority) => (
        <Tag color={priority === 'urgent' ? 'red' : priority === 'high' ? 'orange' : 'blue'}>
          {priority.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => new Date(date).toLocaleDateString(),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Select
            defaultValue={record.status}
            style={{ width: 120 }}
            onChange={(value) => updateIssueStatus(record.id, value)}
          >
            <Option value="submitted">Submitted</Option>
            <Option value="acknowledged">Acknowledged</Option>
            <Option value="in_progress">In Progress</Option>
            <Option value="resolved">Resolved</Option>
            <Option value="closed">Closed</Option>
          </Select>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <h2>Issue Management</h2>
      <Table
        columns={columns}
        dataSource={issues}
        loading={loading}
        rowKey="id"
        pagination={{ pageSize: 10 }}
        scroll={{ x: 800 }}
      />
    </div>
  );
};

export default IssueTable;