# System Architecture Diagrams

**Author:** Farhad Abtahi

## 1. Sequence Diagrams

### 1.1 ECG Reading and Visualization Workflow

```mermaid
sequenceDiagram
    participant User
    participant SCPReader
    participant FileSystem
    participant Parser
    participant Visualizer
    participant Logger

    User->>SCPReader: Initialize with file path
    SCPReader->>FileSystem: Open SCP file
    FileSystem-->>SCPReader: File handle
    
    SCPReader->>Logger: Log read activity start
    SCPReader->>Parser: Parse file header
    Parser-->>SCPReader: Header data (CRC, size)
    
    SCPReader->>Parser: Parse sections
    loop For each section
        Parser->>Parser: Read section ID & size
        Parser->>Parser: Extract section data
        alt Section 1 (Patient Data)
            Parser->>Parser: Parse patient info
        else Section 3 (Lead Info)
            Parser->>Parser: Parse lead definitions
        else Section 6 (Rhythm Data)
            Parser->>Parser: Extract ECG waveforms
        end
        Parser-->>SCPReader: Section data
    end
    
    SCPReader->>Logger: Log successful parsing
    
    User->>SCPReader: Call visualize()
    SCPReader->>Visualizer: Prepare ECG data
    
    alt Medical Paper Format
        Visualizer->>Visualizer: Create 3x4 lead layout
        Visualizer->>Visualizer: Add red grid lines
        Visualizer->>Visualizer: Scale to 25mm/s, 10mm/mV
        Visualizer->>Visualizer: Add rhythm strip
    else Standard Waveform
        Visualizer->>Visualizer: Create stacked layout
        Visualizer->>Visualizer: Add gridlines
        Visualizer->>Visualizer: Apply scaling
    end
    
    Visualizer-->>User: Display/Return figure
    SCPReader->>Logger: Log visualization complete
```

### 1.2 Anonymization Workflow

```mermaid
sequenceDiagram
    participant User
    participant Anonymizer
    participant FileSystem
    participant Logger
    participant MappingFile

    User->>Anonymizer: Initialize with SCP file
    Anonymizer->>FileSystem: Read original file
    FileSystem-->>Anonymizer: File data
    
    Anonymizer->>Logger: Log anonymization start
    
    Anonymizer->>Anonymizer: Generate anonymous ID
    
    Anonymizer->>Anonymizer: Search for patient IDs
    loop For each ID pattern
        Anonymizer->>Anonymizer: Find ID in filename
        Anonymizer->>Anonymizer: Find ID in file content
        Anonymizer->>Anonymizer: Replace with anonymous ID
    end
    
    Anonymizer->>Anonymizer: Clear patient fields
    Note over Anonymizer: Remove: names, DOB, etc.
    
    Anonymizer->>MappingFile: Record ID mapping
    MappingFile-->>Anonymizer: Mapping saved
    
    Anonymizer->>FileSystem: Save anonymized file
    FileSystem-->>Anonymizer: File saved
    
    Anonymizer->>Logger: Log changes made
    Anonymizer->>Logger: Log success
    
    Anonymizer-->>User: Return output path
```

### 1.3 Batch PNG Generation Workflow

```mermaid
sequenceDiagram
    participant User
    participant BatchProcessor
    participant FileSystem
    participant SCPReader
    participant Visualizer
    participant Logger

    User->>BatchProcessor: Run generate_pngs.py
    BatchProcessor->>FileSystem: List SCP files
    FileSystem-->>BatchProcessor: File list
    
    BatchProcessor->>FileSystem: Create output directory
    
    loop For each SCP file
        BatchProcessor->>SCPReader: Initialize reader
        SCPReader->>SCPReader: Parse file
        
        alt Parse successful
            SCPReader-->>BatchProcessor: ECG data
        else Parse failed
            SCPReader->>SCPReader: Generate sample data
            SCPReader-->>BatchProcessor: Sample ECG data
        end
        
        BatchProcessor->>Visualizer: Generate medical format
        Visualizer-->>BatchProcessor: Medical figure
        BatchProcessor->>FileSystem: Save as PNG
        
        BatchProcessor->>Visualizer: Generate waveform format
        Visualizer-->>BatchProcessor: Waveform figure
        BatchProcessor->>FileSystem: Save as PNG
        
        BatchProcessor->>Logger: Log file processed
    end
    
    BatchProcessor->>User: Display summary
```

## 2. Flowcharts

### 2.1 SCP File Parsing Process

```mermaid
flowchart TD
    Start([Start]) --> OpenFile[Open SCP File]
    OpenFile --> ReadHeader[Read File Header]
    ReadHeader --> ValidateCRC{CRC Valid?}
    
    ValidateCRC -->|No| GenerateSample[Generate Sample Data]
    ValidateCRC -->|Yes| ReadSection0[Read Section 0 - Pointers]
    
    ReadSection0 --> ParseSections[Parse Sections]
    ParseSections --> CheckSection{More Sections?}
    
    CheckSection -->|Yes| ReadSectionHeader[Read Section Header]
    ReadSectionHeader --> IdentifySection{Identify Section Type}
    
    IdentifySection -->|Section 1| ParsePatient[Parse Patient Data]
    IdentifySection -->|Section 3| ParseLeads[Parse Lead Info]
    IdentifySection -->|Section 6| ParseRhythm[Parse Rhythm Data]
    IdentifySection -->|Other| SkipSection[Skip Section]
    
    ParsePatient --> StorePtData[Store Patient Info]
    ParseLeads --> StoreLeadData[Store Lead Definitions]
    ParseRhythm --> ExtractECG[Extract ECG Waveforms]
    
    StorePtData --> CheckSection
    StoreLeadData --> CheckSection
    ExtractECG --> CheckSection
    SkipSection --> CheckSection
    
    CheckSection -->|No| ValidateData{ECG Data Present?}
    ValidateData -->|Yes| Success([Success])
    ValidateData -->|No| GenerateSample
    GenerateSample --> Success
```

### 2.2 Visualization Decision Flow

```mermaid
flowchart TD
    Start([User Requests Visualization]) --> CheckData{ECG Data Available?}
    
    CheckData -->|No| ReturnError[Return Error]
    CheckData -->|Yes| CheckStyle{Paper Style?}
    
    CheckStyle -->|Yes| MedicalFormat[Medical Paper Format]
    CheckStyle -->|No| StandardFormat[Standard Waveform]
    
    MedicalFormat --> CreateFigure1[Create Figure 20x11 inches]
    CreateFigure1 --> AddGrid[Add Red Grid Lines]
    AddGrid --> CreateLayout[Create 3x4 Lead Layout]
    CreateLayout --> ProcessLeads1[Process 12 Leads]
    ProcessLeads1 --> AddRhythm[Add Rhythm Strip]
    AddRhythm --> AddMetadata[Add Patient Metadata]
    
    StandardFormat --> CreateFigure2[Create Figure 15x12 inches]
    CreateFigure2 --> StackedLayout[Create Stacked Layout]
    StackedLayout --> ProcessLeads2[Process All Leads]
    ProcessLeads2 --> AddGridlines[Add Gridlines]
    AddGridlines --> AddLabels[Add Lead Labels]
    
    AddMetadata --> CheckShow{Show Display?}
    AddLabels --> CheckShow
    
    CheckShow -->|Yes| Display[Display Plot]
    CheckShow -->|No| ReturnFig[Return Figure Object]
    
    Display --> End([End])
    ReturnFig --> End
    ReturnError --> End
```

### 2.3 Anonymization Process Flow

```mermaid
flowchart TD
    Start([Start Anonymization]) --> ReadFile[Read SCP File]
    ReadFile --> GenerateID[Generate Anonymous ID]
    
    GenerateID --> SearchFilename[Search ID in Filename]
    SearchFilename --> FoundInName{ID Found?}
    
    FoundInName -->|Yes| ReplaceInName[Replace in Filename]
    FoundInName -->|No| CheckContent[Check File Content]
    ReplaceInName --> CheckContent
    
    CheckContent --> SearchContent[Search IDs in Content]
    SearchContent --> FoundInContent{IDs Found?}
    
    FoundInContent -->|Yes| ReplaceInContent[Replace All Occurrences]
    FoundInContent -->|No| ClearFields[Clear Patient Fields]
    ReplaceInContent --> ClearFields
    
    ClearFields --> ProcessFields[Process Each Field]
    ProcessFields --> IsPatientField{Is Patient Field?}
    
    IsPatientField -->|Yes| ClearField[Clear/Replace Field]
    IsPatientField -->|No| KeepField[Keep Field]
    
    ClearField --> MoreFields{More Fields?}
    KeepField --> MoreFields
    
    MoreFields -->|Yes| ProcessFields
    MoreFields -->|No| SaveMapping[Save ID Mapping]
    
    SaveMapping --> SaveFile[Save Anonymized File]
    SaveFile --> LogChanges[Log All Changes]
    LogChanges --> Success([Success])
```

### 2.4 Logging System Flow

```mermaid
flowchart TD
    Start([Activity Start]) --> InitLogger[Initialize ActivityLogger]
    InitLogger --> CheckLogDir{Log Dir Exists?}
    
    CheckLogDir -->|No| CreateDir[Create Log Directory]
    CheckLogDir -->|Yes| GetLogFile[Get Daily Log File]
    CreateDir --> GetLogFile
    
    GetLogFile --> GenerateName[Generate Filename: activity_YYYYMMDD.log]
    GenerateName --> OpenFile[Open Log File in Append Mode]
    
    OpenFile --> LogStart[Log START Entry]
    LogStart --> ExecuteActivity[Execute Activity]
    
    ExecuteActivity --> ActivitySuccess{Success?}
    
    ActivitySuccess -->|Yes| LogDetails[Log Activity Details]
    ActivitySuccess -->|No| LogError[Log Error Details]
    
    LogDetails --> LogSuccess[Log SUCCESS Entry]
    LogError --> LogFailure[Log FAILED Entry]
    
    LogSuccess --> CalculateDuration[Calculate Duration]
    LogFailure --> CalculateDuration
    
    CalculateDuration --> LogDuration[Log Duration]
    LogDuration --> CloseFile[Close Log File]
    CloseFile --> End([End])
```

## 3. System Architecture Overview

```mermaid
graph TB
    subgraph "Input Layer"
        SCP[SCP Files]
        User[User Commands]
    end
    
    subgraph "Core Components"
        Reader[SCP Reader]
        Anonymizer[Anonymizer]
        Visualizer[Visualizer]
        Logger[Logger]
    end
    
    subgraph "Processing"
        Parser[File Parser]
        DataExtractor[Data Extractor]
        IDRemover[ID Remover]
        GridGenerator[Grid Generator]
    end
    
    subgraph "Output Layer"
        PNG[PNG Files]
        AnonFiles[Anonymized SCP]
        Logs[Log Files]
        Display[Display Output]
    end
    
    SCP --> Reader
    User --> Reader
    User --> Anonymizer
    
    Reader --> Parser
    Parser --> DataExtractor
    DataExtractor --> Visualizer
    
    Anonymizer --> IDRemover
    IDRemover --> AnonFiles
    
    Visualizer --> GridGenerator
    GridGenerator --> PNG
    GridGenerator --> Display
    
    Reader --> Logger
    Anonymizer --> Logger
    Visualizer --> Logger
    Logger --> Logs
    
    style Reader fill:#e1f5fe
    style Anonymizer fill:#fff3e0
    style Visualizer fill:#f3e5f5
    style Logger fill:#e8f5e9
```

## 4. Data Flow Diagram

```mermaid
graph LR
    subgraph "Data Sources"
        Original[Original SCP Files]
        Anon[Anonymized SCP Files]
    end
    
    subgraph "Data Processing"
        Parse[Parse Binary Data]
        Extract[Extract ECG Waveforms]
        Transform[Transform to Arrays]
        Normalize[Normalize Signals]
    end
    
    subgraph "Visualization Pipeline"
        Scale[Scale to Medical Units]
        Layout[Apply Layout]
        Grid[Add Grid Lines]
        Render[Render to Image]
    end
    
    subgraph "Outputs"
        Medical[Medical Format PNG]
        Waveform[Waveform Format PNG]
        Stats[Statistics]
    end
    
    Original --> Parse
    Anon --> Parse
    Parse --> Extract
    Extract --> Transform
    Transform --> Normalize
    
    Normalize --> Scale
    Scale --> Layout
    Layout --> Grid
    Grid --> Render
    
    Render --> Medical
    Render --> Waveform
    Transform --> Stats
```

## 5. Component Interaction Diagram

```mermaid
graph TD
    subgraph "User Interface"
        CLI[Command Line]
        Scripts[Python Scripts]
    end
    
    subgraph "Core Modules"
        SCPReader[scp_reader.py]
        SCPAnonymizer[scp_anonymizer.py]
        LogConfig[logging_config.py]
    end
    
    subgraph "Utilities"
        GenPNG[generate_pngs.py]
        ViewLogs[view_logs.py]
    end
    
    subgraph "Data Storage"
        OriginalData[(Original SCP)]
        AnonData[(Anonymized SCP)]
        Images[(PNG Images)]
        LogFiles[(Log Files)]
    end
    
    CLI --> GenPNG
    CLI --> ViewLogs
    Scripts --> SCPReader
    Scripts --> SCPAnonymizer
    
    GenPNG --> SCPReader
    SCPReader --> OriginalData
    SCPReader --> Images
    SCPReader --> LogConfig
    
    SCPAnonymizer --> OriginalData
    SCPAnonymizer --> AnonData
    SCPAnonymizer --> LogConfig
    
    ViewLogs --> LogFiles
    LogConfig --> LogFiles
    
    style SCPReader fill:#bbdefb
    style SCPAnonymizer fill:#ffe0b2
    style LogConfig fill:#c8e6c9
```