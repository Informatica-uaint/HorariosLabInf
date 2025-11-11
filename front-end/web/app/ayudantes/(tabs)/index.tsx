// app/index.tsx (QR Generator Screen)
import React, { useEffect, useState } from 'react';
import { StyleSheet, Text, View, TextInput, Button, Platform, TouchableOpacity, ScrollView, Image } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import QRCode from 'react-native-qrcode-svg';
import { StatusBar } from 'expo-status-bar';

const API_BASE = Platform.OS === 'web'
  ? 'http://10.0.3.54:5000'
  : 'http://10.0.3.54:8081'; // Replace if using Expo Go on mobile

export default function QRGenerator() {
  const [name, setName] = useState('');
  const [surname, setSurname] = useState('');
  const [email, setEmail] = useState('');
  const [savedUsers, setSavedUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [autoRenewal, setAutoRenewal] = useState(false);
  const [renewInterval, setRenewInterval] = useState(null);
  const [qrExpired, setQrExpired] = useState(false);
  
  useEffect(() => {
    loadSavedUsers();
    return () => {
      if (renewInterval) clearInterval(renewInterval);
    };
  }, []);

  const loadSavedUsers = async () => {
    try {
      const storedUsers = await AsyncStorage.getItem('savedUsers');
      if (storedUsers !== null) {
        setSavedUsers(JSON.parse(storedUsers));
      }
    } catch (error) {
      console.error('Error loading users:', error);
    }
  };

  const saveUser = async () => {
    if (name.trim() === '' || surname.trim() === '' || email.trim() === '' || !email.includes('@')) {
      alert('Please enter valid data');
      return;
    }

    const timestamp = Date.now();
    const userData = { 
      name, 
      surname, 
      email, 
      timestamp, 
      expired: false,
      tipoUsuario: 'AYUDANTE' // Identificador de ayudante
    };

    try {
      const newUsers = [...savedUsers, userData];
      await AsyncStorage.setItem('savedUsers', JSON.stringify(newUsers));
      setSavedUsers(newUsers);
      setSelectedUser(userData);
      setQrExpired(false);

      // Clear any existing interval
      if (renewInterval) {
        clearInterval(renewInterval);
        setRenewInterval(null);
      }

      // Set up auto-renewal or QR expiry
      if (autoRenewal) {
        const interval = setInterval(() => {
          const newTimestamp = Date.now();
          setSelectedUser(prevUser => ({
            ...prevUser,
            timestamp: newTimestamp,
            expired: false
          }));
        }, 14000); // Renew every 14 seconds
        setRenewInterval(interval);
      } else {
        // Set expiration after 15 seconds
        setTimeout(() => {
          setQrExpired(true);
          setSelectedUser(prevUser => ({
            ...prevUser,
            expired: true
          }));
        }, 15000);
      }

      setName('');
      setSurname('');
      setEmail('');
    } catch (error) {
      console.error('Error saving user:', error);
    }
  };

  const toggleAutoRenewal = () => {
    const newAutoRenewal = !autoRenewal;
    setAutoRenewal(newAutoRenewal);
    
    // Clear any existing interval
    if (renewInterval) {
      clearInterval(renewInterval);
      setRenewInterval(null);
    }

    if (selectedUser) {
      if (newAutoRenewal) {
        // Activate auto-renewal
        const interval = setInterval(() => {
          const newTimestamp = Date.now();
          setSelectedUser(prevUser => ({
            ...prevUser,
            timestamp: newTimestamp,
            expired: false
          }));
          setQrExpired(false);
        }, 14000);
        setRenewInterval(interval);
      } else if (qrExpired) {
        // Already expired, keep it that way
        setSelectedUser(prevUser => ({
          ...prevUser,
          expired: true
        }));
      } else {
        // Set expiration after 15 seconds
        setTimeout(() => {
          setQrExpired(true);
          setSelectedUser(prevUser => {
            if (prevUser) {
              return {
                ...prevUser,
                expired: true
              };
            }
            return null;
          });
        }, 15000);
      }
    }
  };

  const selectSavedUser = (user) => {
    // Clear any existing interval
    if (renewInterval) {
      clearInterval(renewInterval);
      setRenewInterval(null);
    }
    
    setName(user.name);
    setSurname(user.surname);
    setEmail(user.email);
    
    // When selecting an existing user, generate a new QR with current timestamp
    const timestamp = Date.now();
    const updatedUser = { ...user, timestamp, expired: false, tipoUsuario: 'AYUDANTE' };
    setSelectedUser(updatedUser);
    setQrExpired(false);
    
    // Configure expiration or auto-renewal
    if (autoRenewal) {
      const interval = setInterval(() => {
        const newTimestamp = Date.now();
        setSelectedUser(prevUser => ({
          ...prevUser,
          timestamp: newTimestamp,
          expired: false
        }));
      }, 14000);
      setRenewInterval(interval);
    } else {
      setTimeout(() => {
        setQrExpired(true);
        setSelectedUser(prevUser => ({
          ...prevUser,
          expired: true
        }));
      }, 15000);
    }
  };

  // Generate QR value as a valid JSON object with proper encoding
  const generateQrValue = () => {
    if (!selectedUser) return JSON.stringify({});
  
    // Ensure proper string encoding by removing trailing spaces and normalizing text
    const sanitizedUser = {
      name: selectedUser.name.trim(),
      surname: selectedUser.surname.trim(),
      email: selectedUser.email.trim(),
      timestamp: selectedUser.timestamp,
      tipoUsuario: 'AYUDANTE' // Identificador de ayudante
    };
  
    // Add additional properties based on state
    if (qrExpired && !autoRenewal) {
      return JSON.stringify({
        ...sanitizedUser,
        expired: true,
        status: "EXPIRED"
      });
    }
  
    if (autoRenewal) {
      return JSON.stringify({
        ...sanitizedUser,
        timestamp: Date.now(),
        autoRenewal: true,
        status: "VALID"
      });
    }
  
    return JSON.stringify({
      ...sanitizedUser,
      status: "VALID"
    });
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>QR Generator - Ayudantes</Text>
      <TextInput style={styles.input} placeholder="Name" value={name} onChangeText={setName} />
      <TextInput style={styles.input} placeholder="Surname" value={surname} onChangeText={setSurname} />
      <TextInput style={styles.input} placeholder="Email" value={email} onChangeText={setEmail} keyboardType="email-address" autoCapitalize="none" />
      
      <View style={styles.optionsRow}>
        <Button title="Generate QR" onPress={saveUser} />
        <TouchableOpacity onPress={toggleAutoRenewal} style={[styles.checkboxContainer, autoRenewal && styles.checkboxChecked]}>
          <Text style={styles.checkboxText}>Auto-renew QR</Text>
        </TouchableOpacity>
      </View>

      {savedUsers.length > 0 && (
        <ScrollView horizontal style={styles.userList}>
          {savedUsers.map((user, idx) => (
            <TouchableOpacity 
              key={idx} 
              style={styles.userItem}
              onPress={() => selectSavedUser(user)}
            >
              <Text style={styles.userItemText}>{user.name} {user.surname}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      )}

      {selectedUser && (
        <View style={styles.qrContainer}>
          <Text style={[
            styles.userText, 
            (qrExpired && !autoRenewal) ? styles.expiredText : styles.validText
          ]}>
            {(qrExpired && !autoRenewal) 
              ? 'Expired QR' 
              : `${selectedUser.name} ${selectedUser.surname} - ${selectedUser.email} (AYUDANTE)`
            }
          </Text>
          <QRCode
            value={generateQrValue()}
            size={200}
            backgroundColor="white"
            color={(qrExpired && !autoRenewal) ? "#cccccc" : "black"}
          />
          {autoRenewal && (
            <Text style={styles.renewalText}>QR with active automatic renewal</Text>
          )}
          {!autoRenewal && !qrExpired && (
            <Text style={styles.expirationText}>
              This QR will expire in 15 seconds
            </Text>
          )}
        </View>
      )}
      <StatusBar style="dark" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    padding: 20,
  },
  title: {
    fontSize: 22,
    fontWeight: 'bold',
    marginBottom: 20,
    textAlign: 'center',
  },
  input: {
    height: 50,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 5,
    marginBottom: 10,
    paddingHorizontal: 10,
    backgroundColor: 'white',
  },
  optionsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 15,
  },
  checkboxContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 10,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 5,
    backgroundColor: 'white',
  },
  checkboxChecked: {
    backgroundColor: '#e6f7ff',
    borderColor: '#1890ff',
  },
  checkboxText: {
    marginLeft: 5,
  },
  userList: {
    maxHeight: 50,
    marginVertical: 10,
  },
  userItem: {
    padding: 10,
    marginRight: 10,
    backgroundColor: '#e6f7ff',
    borderRadius: 5,
  },
  userItemText: {
    color: '#1890ff',
  },
  qrContainer: {
    alignItems: 'center',
    marginTop: 20,
    padding: 20,
    backgroundColor: 'white',
    borderRadius: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 2,
  },
  userText: {
    fontSize: 16,
    marginBottom: 15,
    fontWeight: '500',
  },
  expiredText: {
    color: '#ff4d4f',
  },
  validText: {
    color: '#52c41a',
  },
  renewalText: {
    marginTop: 10,
    color: '#1890ff',
    fontStyle: 'italic',
  },
  expirationText: {
    marginTop: 10,
    color: '#999',
    fontStyle: 'italic',
  },
});
