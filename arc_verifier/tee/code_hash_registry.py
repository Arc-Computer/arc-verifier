"""Code hash registry for approved agents.

This module manages the registry of approved code hashes for Shade agents
and other verified containers, matching the pattern used in NEAR contracts.
"""

import hashlib
import json
import fnmatch
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple

from pydantic import BaseModel

from .config import TEEConfig, AgentRegistryConfig, load_config


class AgentStatus(str, Enum):
    """Agent approval status."""
    APPROVED = "approved"
    PENDING = "pending"
    REVOKED = "revoked"
    EXPERIMENTAL = "experimental"


class ApprovedAgent(BaseModel):
    """Approved agent entry in the registry."""
    code_hash: str
    image_tag: str
    agent_name: str
    description: str
    status: AgentStatus
    approved_date: datetime
    expires_date: datetime | None = None
    revoked_date: datetime | None = None
    risk_level: str  # low, medium, high
    capabilities: list[str]  # e.g., ["trading", "cross-chain", "llm"]
    metadata: dict[str, str] = {}


class CodeHashRegistry:
    """Registry of approved agent code hashes.
    
    This registry maintains the list of approved Shade agents and their
    corresponding code hashes, similar to the on-chain registry in NEAR
    contracts.
    """

    def __init__(self, registry_path: Path | None = None, config: TEEConfig | None = None):
        self.config = config or load_config()
        
        if registry_path:
            self.registry_path = registry_path
        elif self.config.registry_path:
            self.registry_path = Path(self.config.registry_path).expanduser()
        else:
            self.registry_path = Path.home() / ".arc-verifier" / "agent_registry.json"
            
        self.registry: dict[str, ApprovedAgent] = {}
        self.agent_config = AgentRegistryConfig()
        self._load_registry()

    def _load_registry(self):
        """Load registry from disk or initialize with defaults."""
        if self.registry_path.exists():
            try:
                with open(self.registry_path) as f:
                    data = json.load(f)
                    for code_hash, agent_data in data.items():
                        # Convert datetime strings back to datetime objects
                        if 'approved_date' in agent_data:
                            agent_data['approved_date'] = datetime.fromisoformat(agent_data['approved_date'])
                        if 'expires_date' in agent_data and agent_data['expires_date']:
                            agent_data['expires_date'] = datetime.fromisoformat(agent_data['expires_date'])
                        if 'revoked_date' in agent_data and agent_data['revoked_date']:
                            agent_data['revoked_date'] = datetime.fromisoformat(agent_data['revoked_date'])

                        self.registry[code_hash] = ApprovedAgent(**agent_data)
            except Exception as e:
                print(f"Failed to load registry: {e}")
                self._initialize_default_registry()
        else:
            self._initialize_default_registry()

    def _initialize_default_registry(self):
        """Initialize registry based on configuration."""
        default_agents = []
        
        # Auto-register local Docker images if enabled
        if self.config.auto_register_local_images:
            default_agents.extend(self._discover_local_agents())
        
        # Add example agents if no local images found
        if not default_agents:
            default_agents.extend(self._create_example_agents())
        
        for agent in default_agents:
            self.registry[agent.code_hash] = agent

        self._save_registry()
    
    def _discover_local_agents(self) -> List[ApprovedAgent]:
        """Discover and register local Docker images matching agent patterns."""
        agents = []
        
        try:
            import docker
            docker_client = docker.from_env()
            
            # Get all local Docker images
            images = docker_client.images.list()
            
            for image in images:
                if not image.tags:
                    continue
                    
                for tag in image.tags:
                    agent = self._create_agent_from_image(tag, image)
                    if agent:
                        agents.append(agent)
                        
        except ImportError:
            print("Docker library not available for auto-discovery")
        except Exception as e:
            print(f"Failed to discover local agents: {e}")
            
        return agents
    
    def _create_agent_from_image(self, tag: str, image) -> Optional[ApprovedAgent]:
        """Create agent entry from Docker image if it matches patterns."""
        
        # Check if image matches any agent patterns
        for pattern_name, pattern_config in self.agent_config.agent_patterns.items():
            pattern = pattern_config["name_pattern"]
            
            if fnmatch.fnmatch(tag.lower(), pattern):
                code_hash = self.calculate_code_hash(tag)
                
                return ApprovedAgent(
                    code_hash=code_hash,
                    image_tag=tag,
                    agent_name=f"{pattern_name.title()} Agent ({tag})",
                    description=f"Auto-discovered {pattern_name} agent",
                    status=AgentStatus.EXPERIMENTAL,  # Auto-discovered agents start as experimental
                    approved_date=datetime.now(),
                    risk_level=pattern_config["default_risk_level"],
                    capabilities=pattern_config["default_capabilities"],
                    metadata={
                        "auto_discovered": "true",
                        "pattern": pattern_name,
                        "tee_platform": pattern_config["tee_platform"]
                    }
                )
        
        return None
    
    def _create_example_agents(self) -> List[ApprovedAgent]:
        """Create example agents for developers to understand the format."""
        agents = []
        
        for example in self.agent_config.example_agents:
            # Use a deterministic hash for examples
            code_hash = hashlib.sha256(f"example:{example['image_tag']}".encode()).hexdigest()
            
            agent = ApprovedAgent(
                code_hash=code_hash,
                image_tag=example["image_tag"],
                agent_name=example["agent_name"],
                description=example["description"],
                status=AgentStatus.PENDING,  # Examples start as pending
                approved_date=datetime.now(),
                risk_level=example["risk_level"],
                capabilities=example["capabilities"],
                metadata=example["metadata"]
            )
            agents.append(agent)
            
        return agents

    def _save_registry(self):
        """Persist registry to disk."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to JSON-serializable format
        data = {}
        for code_hash, agent in self.registry.items():
            agent_dict = agent.model_dump()
            # Convert datetime to ISO format
            agent_dict['approved_date'] = agent_dict['approved_date'].isoformat()
            if agent_dict.get('expires_date'):
                agent_dict['expires_date'] = agent_dict['expires_date'].isoformat()
            if agent_dict.get('revoked_date'):
                agent_dict['revoked_date'] = agent_dict['revoked_date'].isoformat()
            data[code_hash] = agent_dict

        with open(self.registry_path, 'w') as f:
            json.dump(data, f, indent=2)

    def verify_code_hash(self, code_hash: str) -> tuple[bool, ApprovedAgent | None, list[str]]:
        """Verify if a code hash is approved.
        
        Returns:
            Tuple of (is_approved, agent_info, warnings)
        """
        warnings = []

        agent = self.registry.get(code_hash)
        if not agent:
            return False, None, ["Unknown code hash - agent not in registry"]

        # Check status
        if agent.status == AgentStatus.REVOKED:
            return False, agent, ["Agent has been revoked"]

        if agent.status == AgentStatus.EXPERIMENTAL:
            warnings.append("Agent is experimental - use with caution")

        # Check expiration
        if agent.expires_date and datetime.now() > agent.expires_date:
            return False, agent, ["Agent approval has expired"]

        # Check if pending
        if agent.status == AgentStatus.PENDING:
            warnings.append("Agent approval is pending - limited functionality")

        is_approved = agent.status in [AgentStatus.APPROVED, AgentStatus.EXPERIMENTAL]

        return is_approved, agent, warnings

    def calculate_code_hash(self, image_path: str) -> str:
        """Calculate code hash from Docker image."""
        try:
            import docker
            docker_client = docker.from_env()

            try:
                # Get the image
                image_info = docker_client.images.get(image_path)

                # Use the image ID (sha256) as the code hash
                if hasattr(image_info, 'id'):
                    # Remove 'sha256:' prefix if present
                    image_id = image_info.id
                    if image_id.startswith('sha256:'):
                        return image_id[7:]  # Remove 'sha256:' prefix
                    return image_id

            except docker.errors.ImageNotFound:
                # Image not found locally, use name-based hash
                pass
            except docker.errors.APIError:
                # API error, fall back to name-based hash
                pass

        except ImportError:
            # Docker library not available
            pass

        # Fallback to hash of image path
        return hashlib.sha256(f"image:{image_path}".encode()).hexdigest()

    def add_agent(self, agent: ApprovedAgent) -> bool:
        """Add a new agent to the registry."""
        try:
            self.registry[agent.code_hash] = agent
            self._save_registry()
            return True
        except Exception:
            return False

    def remove_agent(self, code_hash: str) -> bool:
        """Remove an agent from the registry."""
        try:
            if code_hash in self.registry:
                del self.registry[code_hash]
                self._save_registry()
                return True
            return False
        except Exception:
            return False

    def list_agents(self) -> list[ApprovedAgent]:
        """List all agents in the registry."""
        return list(self.registry.values())

    def get_agent(self, code_hash: str) -> ApprovedAgent | None:
        """Get specific agent by code hash."""
        return self.registry.get(code_hash)
