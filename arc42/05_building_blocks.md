# 5. Building Block View

## 5.1 Level 1: System Context
The flow cytometer system consists of:
- **Control Software**: Python-based multi-agent orchestration
- **Firmware Layer**: Real-time hardware control (laser, fluidics, optics)
- **Data Pipeline**: Event acquisition, compensation, gating
- **User Interface**: Protocol definition and result visualization

## 5.2 Level 2: Control Software Decomposition
| Component | Responsibility |
|-----------|---------------|
| AgentOrchestrator | Coordinates multi-agent workflow via LangGraph |
| BaseAgent | Common agent infrastructure (persona, memory, LLM) |
| SafetyModule | Validates physical operations before execution |
| MemoryModule | Short-term context + long-term skills persistence |
| ObservabilityModule | Phoenix tracing for all LLM interactions |

## 5.3 Level 2: Firmware Interfaces
| Interface | Protocol | Constraints |
|-----------|----------|-------------|
| LaserControl | Serial/USB | Power: 0-100 mW, interlock required |
| FluidicsControl | Serial | Flow rate: 1-100 uL/min, pressure: 0-30 PSI |
| PMTControl | SPI | Voltage: 0-1000 V |
| DataAcquisition | DMA | Max 50,000 events/s |
