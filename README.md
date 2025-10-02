# TACTICAL RAG DOCUMENT INTELLIGENCE SYSTEM

## Quick Start

**For Operators (End Users):** See `docs/OPERATOR-GUIDE.md`

**For Maintainers (IT/Technical):** See `docs/MAINTAINER-GUIDE.md`

---

## One-Click Deployment

1. **Start System:** Double-click `deploy.bat`
2. **Change Documents:** Double-click `swap-mission.bat`
3. **Stop System:** Double-click `stop.bat`

---

## Directory Structure

```
â”œâ”€â”€ deploy.bat                 â† Double-click to start
â”œâ”€â”€ swap-mission.bat          â† Double-click to change documents
â”œâ”€â”€ stop.bat                  â† Double-click to stop
â”œâ”€â”€ documents/                â† Add your documents here
â”œâ”€â”€ chroma_db/                â† Database (auto-generated)
â”œâ”€â”€ docs/                     â† Full documentation
â”œâ”€â”€ _deployment/              â† Docker images (don't touch)
â”œâ”€â”€ _config/                  â† Configuration files (don't touch)
â””â”€â”€ _src/                     â† Source code (don't touch)
```

---

## Requirements

- Windows 10/11
- Docker Desktop installed and running
- 8 GB RAM minimum (16 GB recommended)

---

## First Time Setup

1. Ensure Docker Desktop is running
2. Place documents in the `documents/` folder
3. Double-click `deploy.bat`
4. Wait 3-5 minutes for initial setup
5. Browser opens automatically

---

## Support

- **Operators:** See `docs/OPERATOR-GUIDE.md`
- **Technical Issues:** See `docs/MAINTAINER-GUIDE.md`
- **Emergency Reset:** Run `swap-mission.bat` then `deploy.bat`

---

**WARNING:** This is a U.S. Government Information System. 
Unauthorized access is prohibited. By using this system, you consent to monitoring.
