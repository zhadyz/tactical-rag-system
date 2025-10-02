# TACTICAL RAG DOCUMENT INTELLIGENCE SYSTEM
## OPERATOR GUIDE

---

## WHAT IS THIS SYSTEM?

This system lets you ask questions about your documents and get instant answers from an AI. Think of it as having an expert who has read all your mission documents and can answer any question about them immediately.

**What it does:**
- Reads PDF files, Word documents, and text files
- Works with scanned documents (uses OCR to read images)
- Answers questions based on what's in your documents
- Shows you which documents it used to answer
- Works completely offline (no internet needed)

---

## QUICK START (FIRST TIME)

### What You Need:
- A computer with Windows
- Docker Desktop installed (ask IT if you don't have it)
- This deployment package on a USB drive

### Steps:

**1. Copy the deployment folder from USB to your computer**
   - Copy the entire folder to your Desktop or Documents

**2. Make sure Docker Desktop is running**
   - Look for the Docker whale icon in your taskbar (bottom right)
   - If you don't see it, open Docker Desktop from Start Menu
   - Wait until it says "Docker Desktop is running"

**3. Add your documents**
   - Open the `documents` folder
   - Copy your mission documents into this folder
   - Supported files: PDF, Word (.docx), Text (.txt), Markdown (.md)

**4. Start the system**
   - Double-click `deploy.bat`
   - Wait 3-5 minutes for first-time setup
   - A browser window will open automatically

**5. Start asking questions**
   - Type your question in the text box
   - Click "EXECUTE" or press Enter
   - The system will answer based on your documents

---

## DAILY USE

### Starting the System:
1. Make sure Docker Desktop is running
2. Double-click `deploy.bat`
3. Wait 30-60 seconds
4. Browser opens automatically at http://localhost:7860

### Stopping the System:
1. Double-click `stop.bat`
2. System shuts down safely

### Changing Documents (New Mission):
1. Double-click `swap-mission.bat`
2. Remove old documents from the `documents` folder
3. Add new mission documents
4. Double-click `deploy.bat` to restart

---

## HOW TO USE THE INTERFACE

### Main Screen:

**Left Side - Chat Area:**
- Type your questions in the text box at the bottom
- Click "EXECUTE" to send
- Answers appear in the chat window
- Sources are listed at the bottom of each answer

**Right Side - Document List:**
- Shows all your indexed documents
- File sizes displayed
- Different icons for different file types:
  - 📄 Text files
  - 📕 PDF files
  - 📘 Word documents
  - 📗 Markdown files

**Example Questions (Click These):**
- "What topics are covered in the documents?"
- "Summarize the key points"
- "What information is available?"

**System Status (Top):**
- Green "OPERATIONAL" = System ready
- Red "OFFLINE" = System not ready (wait or check Docker)
- Shows number of documents and last update time

---

## TIPS FOR BETTER RESULTS

### Asking Good Questions:
- **Be specific:** "What are the medical requirements for deployment?" instead of "Tell me about requirements"
- **Reference topics:** "Summarize the section about vehicle maintenance"
- **Ask for sources:** The system automatically shows which documents it used

### What Works Well:
- Finding specific information across multiple documents
- Summarizing long documents
- Comparing information between documents
- Extracting data points (dates, names, procedures)

### What Doesn't Work:
- Questions about things not in your documents
- Real-time information (weather, current events)
- Documents you haven't uploaded yet
- Password-protected PDFs

---

## COMMON ISSUES

### "The page won't load"
**Fix:**
- Check if Docker Desktop is running (whale icon in taskbar)
- Wait 1-2 minutes - system might still be starting
- Try manually going to http://localhost:7860
- Run `stop.bat` then `deploy.bat` to restart

### "System says no documents found"
**Fix:**
- Check that documents are in the `documents` folder
- Make sure files are PDF, DOCX, TXT, or MD format
- Run `swap-mission.bat` to re-index

### "Answers don't match my documents"
**Fix:**
- You likely added documents after the system started
- Run `swap-mission.bat` to clear and re-index
- Check that the right documents are shown in the document list

### "System is very slow"
**This is normal for:**
- First startup (downloads AI models, 15-30 minutes)
- Scanned PDFs (OCR takes 1-2 minutes per page)
- Large document sets (indexing takes time)

**If it's always slow:**
- Close other programs using memory
- Check computer has at least 8GB RAM available
- Restart Docker Desktop

---

## WHAT FILES DO WHAT

**deploy.bat** - Start the system (double-click this)
**stop.bat** - Stop the system safely
**swap-mission.bat** - Change to different documents
**documents/** - Put your files here
**docker-compose.yml** - System configuration (don't touch)
**README.md** - This file

**Don't delete these:**
- rag-app-image.tar
- ollama-image.tar
- ollama-models.tar.gz

---

## IMPORTANT NOTES

### Security:
- Everything runs on your computer (no internet needed)
- Your documents never leave your machine
- No data is sent to any server
- System works completely offline after setup

### Document Handling:
- Maximum file size: 50 MB per file
- Scanned PDFs work but take longer to process
- Password-protected files won't work
- System reads text content only (no images)

### System Requirements:
- Windows 10 or 11
- 8 GB RAM minimum (16 GB recommended)
- 20 GB free disk space
- Docker Desktop installed

---

## GETTING HELP

### If Nothing Works:
1. Restart Docker Desktop
2. Run `stop.bat`
3. Run `deploy.bat`
4. Wait 2 minutes and try again

### If Still Broken:
Contact your IT support or system maintainer with:
- What you were trying to do
- What error message you saw
- Screenshot of the problem

### Emergency Reset:
If everything is broken and you need to start fresh:
1. Run `stop.bat`
2. Delete the `chroma_db` folder
3. Run `deploy.bat`

This will re-index your documents from scratch.

---

## WORKFLOW SUMMARY

**Normal Day:**
```
1. Start Docker Desktop
2. Double-click deploy.bat
3. Wait for browser to open
4. Ask questions
5. Double-click stop.bat when done
```

**New Mission:**
```
1. Double-click swap-mission.bat
2. Replace documents in documents/ folder
3. Double-click deploy.bat
4. System re-indexes (1-5 minutes)
5. Ready to use
```

**System Not Working:**
```
1. Double-click stop.bat
2. Check Docker Desktop is running
3. Double-click deploy.bat
4. Wait 2 minutes
```

---

## REMEMBER

- System works offline (no internet after setup)
- Documents stay on your computer
- Re-index when you change documents
- Green "OPERATIONAL" means ready to use
- Ask specific questions for best answers
- Sources are shown for verification

###########################################################################################################

For technical issues, contact:

AMN BARI

Abdul.bari@us.af.mil
Cyber Defense Operator / Network Infrastructure
