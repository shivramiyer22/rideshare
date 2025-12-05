# 🔗 MongoDB Atlas Setup Guide

**Status:** Quick 2-minute setup to connect your MongoDB Atlas account

---

## 🎯 What You Need

Your **MongoDB Atlas Connection String** from your account.

---

## 📋 Step-by-Step Guide

### **Step 1: Get Your MongoDB Atlas Connection String**

1. **Log in to MongoDB Atlas:**
   - Go to: https://cloud.mongodb.com/
   - Log in with your account

2. **Navigate to your Cluster:**
   - Click on "Database" in the left sidebar
   - Find your cluster (or create a new one if needed)

3. **Get Connection String:**
   - Click the **"Connect"** button on your cluster
   - Select **"Connect your application"**
   - Choose **Driver: Python**
   - Choose **Version: 3.12 or later**
   - Copy the connection string

   It will look like:
   ```
   mongodb+srv://username:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```

4. **Important:** Replace `<password>` with your actual database password

---

### **Step 2: Create .env File**

I'll create the `.env` file for you now. You just need to paste your connection string!

The file will be created at:
```
/Users/ishitasharma/Documents/GitHub/rideshare/rideshare/backend/.env
```

---

### **Step 3: Update the Connection String**

After I create the file, you'll need to:
1. Open `backend/.env`
2. Find the line: `MONGODB_URL=`
3. Replace with your MongoDB Atlas connection string

Example:
```bash
# BEFORE (placeholder):
MONGODB_URL=mongodb+srv://username:password@cluster.xxxxx.mongodb.net/

# AFTER (your actual connection):
MONGODB_URL=mongodb+srv://yourusername:yourpassword@cluster0.abc123.mongodb.net/rideshare?retryWrites=true&w=majority
```

**Important Notes:**
- Replace `username` with your MongoDB Atlas username
- Replace `password` with your database password
- Add `/rideshare` after `.net/` (this is the database name)
- Keep `?retryWrites=true&w=majority` at the end

---

### **Step 4: Restart Backend**

After updating the `.env` file:

```bash
# The backend should automatically pick up the new connection
# If it doesn't restart automatically, stop and restart it:

# In Terminal 5 (or wherever backend is running):
# Press Ctrl+C to stop
# Then run:
cd /Users/ishitasharma/Documents/GitHub/rideshare/rideshare/backend
./start.sh
```

---

### **Step 5: Verify Connection**

Once backend restarts, you should see:
```
✅ Successfully connected to MongoDB
✅ Database: rideshare
```

Then test the API:
```bash
curl http://localhost:8000/api/orders/queue/priority
```

Should return:
```json
{
  "P0": [],
  "P1": [],
  "P2": [],
  "status": {"P0": 0, "P1": 0, "P2": 0}
}
```

---

## 🎉 Done!

Once connected, the **Priority Queue Visualization** will work perfectly!

---

## 🔒 Security Notes

**DO NOT commit your `.env` file to Git!**
- The `.env` file contains your database password
- It's already in `.gitignore`
- Never share your connection string publicly

---

## 🐛 Troubleshooting

### Issue: "Authentication failed"
- **Solution:** Check your username and password in the connection string
- Make sure you're using the database user password (not your MongoDB Atlas account password)

### Issue: "Network timeout"
- **Solution:** Add your IP address to MongoDB Atlas whitelist:
  1. Go to MongoDB Atlas → Network Access
  2. Click "Add IP Address"
  3. Either add your current IP or use `0.0.0.0/0` (allow all - for testing only)

### Issue: "Database does not exist"
- **Solution:** MongoDB Atlas will automatically create the `rideshare` database when you first insert data
- Just create your first order and it will create the database

---

## ✅ Quick Checklist

- [ ] Logged into MongoDB Atlas
- [ ] Got connection string
- [ ] Updated backend/.env file with connection string
- [ ] Replaced `<password>` with actual password
- [ ] Added `/rideshare` database name to connection string
- [ ] Restarted backend
- [ ] Backend shows "Successfully connected to MongoDB"
- [ ] Tested API endpoint
- [ ] Ready to use Queue Visualization!

---

**Need help? Let me know which step you're on!**

