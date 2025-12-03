# 🚀 Quick MongoDB Atlas Setup (2 Minutes!)

**You said you have a MongoDB account - Perfect! Let's connect it!**

---

## ⚡ Super Quick Steps

### **Step 1: Get Your Connection String**

1. Go to **MongoDB Atlas**: https://cloud.mongodb.com/
2. Log in with your account
3. Click **"Database"** in sidebar
4. Find your cluster (or create free cluster if needed)
5. Click **"Connect"** button
6. Choose **"Connect your application"**
7. Copy the connection string (looks like this):
   ```
   mongodb+srv://username:<password>@cluster0.xxxxx.mongodb.net/
   ```

8. **Replace `<password>`** with your actual database password
9. **Add `/rideshare`** at the end
10. **Add query params** if not already there: `?retryWrites=true&w=majority`

**Final format should look like:**
```
mongodb+srv://yourusername:yourpassword@cluster0.abc123.mongodb.net/rideshare?retryWrites=true&w=majority
```

---

### **Step 2: Create/Edit `.env` File**

1. **Open this file:**
   ```
   /Users/ishitasharma/Documents/GitHub/rideshare/rideshare/backend/.env
   ```

2. **If file doesn't exist, create it with this content:**
   ```bash
   # MongoDB Atlas Connection
   MONGODB_URL=YOUR_CONNECTION_STRING_HERE
   MONGODB_DB_NAME=rideshare

   # Redis (local)
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_DB=0

   # ChromaDB
   CHROMADB_PATH=./chroma_db

   # API
   SECRET_KEY=your-secret-key-change-in-production
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30

   # Optional (not needed for Queue Visualization)
   OPENAI_API_KEY=optional-for-ai-features
   LANGSMITH_API_KEY=optional
   LANGSMITH_TRACING=false
   LANGSMITH_PROJECT=rideshare
   ```

3. **Replace `YOUR_CONNECTION_STRING_HERE`** with your actual MongoDB Atlas connection string from Step 1

---

### **Step 3: Restart Backend**

The backend is currently running in **Terminal 5**.

**Option A - Let it Auto-Restart:**
- Just save the `.env` file
- The backend should detect changes and restart

**Option B - Manual Restart:**
```bash
# Press Ctrl+C in Terminal 5 to stop
# Then run:
cd /Users/ishitasharma/Documents/GitHub/rideshare/rideshare/backend
./start.sh
```

---

### **Step 4: Verify It Works!**

After backend restarts, check the logs in Terminal 5. You should see:
```
✅ Successfully connected to MongoDB
Database: rideshare
```

Then test the API:
```bash
curl http://localhost:8000/api/orders/queue/priority
```

Should return (empty queues initially):
```json
{
  "P0": [],
  "P1": [],
  "P2": [],
  "status": {"P0": 0, "P1": 0, "P2": 0}
}
```

---

### **Step 5: Use Queue Visualization! 🎉**

1. **Open browser:** http://localhost:3000
2. **Navigate to "Queue" tab**
3. **See 3 colored columns:** 🔴 P0, 🟡 P1, 🟢 P2

**To test with data:**
4. Go to **"Orders" tab**
5. Create 2-3 orders:
   - Choose "CONTRACTED" → Goes to P0 (red)
   - Choose "STANDARD" → Goes to P1 (amber)
   - Choose "CUSTOM" → Goes to P2 (green)
6. Return to **"Queue" tab**
7. **See your orders!** They auto-refresh every 5 seconds

---

## 🔒 Security Tip

**Add your IP to MongoDB Atlas whitelist:**
1. MongoDB Atlas → **Network Access**
2. Click **"Add IP Address"**
3. Add **your current IP** or `0.0.0.0/0` (all IPs - for testing)

---

## 📝 Quick Command to Create .env

If you want to create the file quickly via terminal:

```bash
cd /Users/ishitasharma/Documents/GitHub/rideshare/rideshare/backend

# Create .env file
cat > .env << 'EOF'
MONGODB_URL=YOUR_MONGODB_ATLAS_CONNECTION_STRING_HERE
MONGODB_DB_NAME=rideshare
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
CHROMADB_PATH=./chroma_db
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
OPENAI_API_KEY=optional
LANGSMITH_API_KEY=optional
LANGSMITH_TRACING=false
LANGSMITH_PROJECT=rideshare
EOF

# Then edit it to add your real connection string:
nano .env
# or
open -e .env
```

---

## ✅ That's It!

Once you update the `.env` file with your MongoDB Atlas connection string:
1. ✅ Backend connects to your cloud database
2. ✅ Queue Visualization works perfectly
3. ✅ All order data is stored in your MongoDB Atlas

**No local MongoDB installation needed!** ☁️

---

## 🆘 Need Help?

**Common Issues:**

**"Authentication failed"**
→ Check username/password in connection string

**"Network timeout"**
→ Add your IP to MongoDB Atlas whitelist

**"Can't find .env file"**
→ Create it in: `/Users/ishitasharma/Documents/GitHub/rideshare/rideshare/backend/.env`

---

**Ready? Just need your MongoDB Atlas connection string!** 🚀

Let me know when you've added it to the `.env` file, and I'll help verify everything works!

