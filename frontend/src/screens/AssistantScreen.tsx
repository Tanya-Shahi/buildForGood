import React, { useState } from 'react';
import { View, TextInput, TouchableOpacity, FlatList, Text, StyleSheet } from 'react-native';
import apiClient from '../api/client';

export default function AssistantScreen() {
  const [messages, setMessages] = useState<{id: string, text: string, sender: 'user' | 'ai'}[]>([]);
  const [input, setInput] = useState('');

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMsg = { id: Date.now().toString(), text: input, sender: 'user' as const };
    setMessages(prev => [userMsg, ...prev]);
    setInput('');

    try {
      // Connects to your backend gemini_service.py
      const response = await apiClient.post('/support/ask-gemini', { query: input });
      const aiMsg = { id: (Date.now() + 1).toString(), text: response.data.answer, sender: 'ai' as const };
      setMessages(prev => [aiMsg, ...prev]);
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <View style={styles.container}>
      <FlatList
        data={messages}
        inverted
        keyExtractor={item => item.id}
        contentContainerStyle={styles.listContent}
        renderItem={({ item }) => (
          <View style={[styles.bubble, item.sender === 'user' ? styles.userBubble : styles.aiBubble]}>
            <Text style={item.sender === 'user' ? styles.userText : styles.aiText}>
              {item.text}
            </Text>
          </View>
        )}
      />
      <View style={styles.inputContainer}>
        <TextInput 
          style={styles.input} 
          value={input} 
          onChangeText={setInput} 
          placeholder="Ask about safety..." 
        />
        <TouchableOpacity style={styles.sendButton} onPress={sendMessage}>
          <Text style={styles.sendText}>Send</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f3f4f6' },
  listContent: { padding: 8 },
  bubble: { padding: 12, borderRadius: 16, marginVertical: 4, maxWidth: '80%' },
  userBubble: { alignSelf: 'flex-end', backgroundColor: '#2563eb' },
  aiBubble: { alignSelf: 'flex-start', backgroundColor: '#e5e7eb' },
  userText: { color: '#ffffff', fontSize: 16 },
  aiText: { color: '#1f2937', fontSize: 16 },
  inputContainer: { flexDirection: 'row', padding: 16, backgroundColor: '#fff', borderTopWidth: 1, borderTopColor: '#e5e7eb' },
  input: { flex: 1, borderWidth: 1, borderColor: '#d1d5db', borderRadius: 8, padding: 10, backgroundColor: '#f9fafb' },
  sendButton: { marginLeft: 8, justifyContent: 'center', paddingHorizontal: 16, backgroundColor: '#2563eb', borderRadius: 8 },
  sendText: { color: '#fff', fontWeight: '600' }
});