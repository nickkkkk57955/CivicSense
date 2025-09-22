import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  Image,
  StyleSheet,
  RefreshControl,
} from 'react-native';

const IssueFeed = ({ navigation }) => {
  const [issues, setIssues] = useState([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState('trending');

  useEffect(() => {
    fetchIssues();
  }, [activeTab]);

  const fetchIssues = async () => {
    setLoading(true);
    try {
      const endpoint = `http://localhost:8000/social/feed/${activeTab}`;
      const response = await fetch(endpoint, {
        headers: {
          'Authorization': `Bearer ${await getToken()}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setIssues(data);
      }
    } catch (error) {
      console.error('Fetch error:', error);
    }
    setLoading(false);
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchIssues();
    setRefreshing(false);
  };

  const voteOnIssue = async (issueId, voteType) => {
    try {
      const response = await fetch(`http://localhost:8000/social/issues/${issueId}/vote`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${await getToken()}`,
        },
        body: JSON.stringify({ vote_type: voteType }),
      });

      if (response.ok) {
        fetchIssues(); // Refresh the feed
      }
    } catch (error) {
      console.error('Vote error:', error);
    }
  };

  const getToken = async () => {
    // Implement token retrieval
    return 'your-jwt-token';
  };

  const getStatusColor = (status) => {
    const colors = {
      submitted: '#ff6b6b',
      acknowledged: '#ffa726',
      in_progress: '#42a5f5',
      resolved: '#66bb6a',
      closed: '#78909c',
    };
    return colors[status] || '#666';
  };

  const renderIssue = ({ item }) => (
    <View style={styles.issueCard}>
      <View style={styles.cardHeader}>
        <Text style={styles.issueTitle}>{item.title}</Text>
        <View style={[styles.statusBadge, { backgroundColor: getStatusColor(item.status) }]}>
          <Text style={styles.statusText}>{item.status.toUpperCase()}</Text>
        </View>
      </View>

      <Text style={styles.issueDescription}>{item.description}</Text>

      <View style={styles.issueInfo}>
        <Text style={styles.infoText}>👤 {item.reporter_name}</Text>
        <Text style={styles.infoText}>📍 {item.address}</Text>
        <Text style={styles.infoText}>⭐ {item.reporter_karma} karma</Text>
      </View>

      <View style={styles.voteButtons}>
        <TouchableOpacity
          style={[styles.voteButton, styles.upvoteButton]}
          onPress={() => voteOnIssue(item.id, 'upvote')}
        >
          <Text style={styles.voteButtonText}>👍 Important ({item.upvotes})</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.voteButton, styles.confirmButton]}
          onPress={() => voteOnIssue(item.id, 'confirm')}
        >
          <Text style={styles.voteButtonText}>✅ Me Too! ({item.confirmations})</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Civic Issues</Text>
      </View>

      <View style={styles.tabContainer}>
        {['trending', 'newest', 'nearby'].map((tab) => (
          <TouchableOpacity
            key={tab}
            style={[styles.tab, activeTab === tab && styles.activeTab]}
            onPress={() => setActiveTab(tab)}
          >
            <Text style={[styles.tabText, activeTab === tab && styles.activeTabText]}>
              {tab === 'trending' && '🔥'} {tab === 'newest' && '🆕'} {tab === 'nearby' && '📍'} {tab.toUpperCase()}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <FlatList
        data={issues}
        renderItem={renderIssue}
        keyExtractor={(item) => item.id.toString()}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        showsVerticalScrollIndicator={false}
      />

      <TouchableOpacity
        style={styles.fab}
        onPress={() => navigation.navigate('ReportIssue')}
      >
        <Text style={styles.fabText}>+</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#667eea',
    padding: 20,
    paddingTop: 50,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: 'white',
    textAlign: 'center',
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: 'white',
    paddingHorizontal: 10,
  },
  tab: {
    flex: 1,
    padding: 15,
    alignItems: 'center',
  },
  activeTab: {
    borderBottomWidth: 3,
    borderBottomColor: '#667eea',
  },
  tabText: {
    fontSize: 14,
    color: '#666',
  },
  activeTabText: {
    color: '#667eea',
    fontWeight: 'bold',
  },
  issueCard: {
    backgroundColor: 'white',
    margin: 10,
    padding: 15,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 10,
  },
  issueTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    flex: 1,
    marginRight: 10,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    color: 'white',
    fontSize: 10,
    fontWeight: 'bold',
  },
  issueDescription: {
    fontSize: 14,
    color: '#666',
    marginBottom: 10,
  },
  issueInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 15,
  },
  infoText: {
    fontSize: 12,
    color: '#888',
  },
  voteButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  voteButton: {
    flex: 1,
    padding: 10,
    borderRadius: 20,
    alignItems: 'center',
    marginHorizontal: 5,
  },
  upvoteButton: {
    backgroundColor: '#4caf50',
  },
  confirmButton: {
    backgroundColor: '#2196f3',
  },
  voteButtonText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 12,
  },
  fab: {
    position: 'absolute',
    bottom: 20,
    right: 20,
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#667eea',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 6,
    elevation: 8,
  },
  fabText: {
    fontSize: 24,
    color: 'white',
    fontWeight: 'bold',
  },
});

export default IssueFeed;