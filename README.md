# Tactical RAG Document Intelligence System

![CI Pipeline](https://github.com/zhadyz/tactical-rag-system/actions/workflows/ci.yml/badge.svg)

Enterprise RAG document intelligence system with adaptive retrieval strategies.

---

## Quick Start

**End Users:** See `docs/OPERATOR-GUIDE.md`  
**Technical Staff:** See `docs/MAINTAINER-GUIDE.md`

### Deployment Commands

| Action | Command |
|--------|---------|
| Start System | `deploy.bat` |
| Change Documents | `swap-mission.bat` |
| Stop System | `stop.bat` |

---

## Project Structure
tactical-rag-system/
│
├── deploy.bat              # System startup
├── swap-mission.bat        # Document swap utility
├── stop.bat                # System shutdown
│
├── documents/              # Place your documents here
├── chroma_db/              # Vector database (auto-generated)
├── docs/                   # Documentation
│
├── _deployment/            # Docker images
├── _config/                # System configuration
└── _src/                   # Application source code

---

## System Requirements

- **OS:** Windows 10/11
- **Software:** Docker Desktop (running)
- **Memory:** 8 GB minimum, 16 GB recommended
- **Disk:** 10 GB free space

---

## First-Time Setup

1. Install and start Docker Desktop
2. Add documents to `documents/` folder
3. Run `deploy.bat`
4. Wait 3-5 minutes for initialization
5. Browser opens automatically at `http://localhost:7860`

---

## Features

- Adaptive retrieval (simple/hybrid/advanced strategies)
- Multi-format document support (PDF, DOCX, TXT, MD)
- Real-time settings adjustment
- Automatic document indexing
- Source citation with relevance scores

---

## Support

**Operational Issues:** `docs/OPERATOR-GUIDE.md`  
**Technical Issues:** `docs/MAINTAINER-GUIDE.md`  
**System Reset:** Run `swap-mission.bat` then `deploy.bat`

---

## Warning Notice

**This is a U.S. Government Information System (IS) that is provided for USG-authorized use only.**

By using this IS (which includes any device attached to this IS), you consent to the following conditions:

- The USG routinely intercepts and monitors communications on this IS for purposes including, but not limited to, penetration testing, COMSEC monitoring, network operations and defense, personnel misconduct (PM), law enforcement (LE), and counterintelligence (CI) investigations.

- At any time, the USG may inspect and seize data stored on this IS.

- Communications using, or data stored on, this IS are not private, are subject to routine monitoring, interception, and search, and may be disclosed or used for any USG-authorized purpose.

- This IS includes security measures (e.g., authentication and access controls) to protect USG interests--not for your personal benefit or privacy.

**Unauthorized or improper use of this system is prohibited and may result in disciplinary action and/or civil and criminal penalties.**
