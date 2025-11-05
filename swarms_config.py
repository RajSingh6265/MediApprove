"""
Swarms Configuration for Clinical Document Processing
Configures all agents and their tools
"""

from swarms import Agent
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClinicalDocumentAgent(Agent):
    """Base agent for clinical document processing"""
    
    def __init__(self, name, description, task_type):
        super().__init__(
            agent_name=name,
            description=description,
            max_retries=3,
            timeout=300,
            task_type=task_type
        )
        self.name = name
        self.task_type = task_type


def create_pdf_extraction_agent():
    """Agent for PDF extraction"""
    agent = ClinicalDocumentAgent(
        name="PDF Extraction Agent",
        description="Extracts text and data from clinical PDF documents",
        task_type="pdf_extraction"
    )
    return agent


def create_image_ocr_agent():
    """Agent for Image OCR"""
    agent = ClinicalDocumentAgent(
        name="Image OCR Agent",
        description="Extracts text from medical prescription and note images using OCR",
        task_type="image_ocr"
    )
    return agent


def create_fhir_conversion_agent():
    """Agent for FHIR conversion"""
    agent = ClinicalDocumentAgent(
        name="FHIR Conversion Agent",
        description="Converts extracted clinical data to FHIR standard format",
        task_type="fhir_conversion"
    )
    return agent


def create_validation_agent():
    """Agent for validation"""
    agent = ClinicalDocumentAgent(
        name="Validation Agent",
        description="Validates extracted data and FHIR resources for quality and completeness",
        task_type="validation"
    )
    return agent


def create_logging_agent():
    """Agent for logging and monitoring"""
    agent = ClinicalDocumentAgent(
        name="Logging Agent",
        description="Logs all operations, errors, and results for audit trail",
        task_type="logging"
    )
    return agent


# Agent registry
AGENTS = {
    "pdf_extraction": create_pdf_extraction_agent(),
    "image_ocr": create_image_ocr_agent(),
    "fhir_conversion": create_fhir_conversion_agent(),
    "validation": create_validation_agent(),
    "logging": create_logging_agent()
}


def get_agent(agent_type):
    """Get agent by type"""
    if agent_type not in AGENTS:
        raise ValueError(f"Unknown agent type: {agent_type}")
    return AGENTS[agent_type]


if __name__ == "__main__":
    # Test configuration
    print("✅ Testing Swarms configuration...")
    for agent_type, agent in AGENTS.items():
        print(f"   • {agent_type}: {agent.name}")
    print("✅ All agents initialized successfully!")
