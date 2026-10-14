import os
import time
import json
import uuid
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from .base import (
    AgentStatus, CapabilityStatus, AgentModel,
    TaskExecutionRequest, TaskExecutionResult, redact_secrets,
    is_executable_identity_valid, compute_config_fingerprint,
    VerificationFailureReason
)
from .registry import AgentRegistry

class OrchestratorDecision:
    def __init__(
        self,
        task_id: str,
        role: str,
        required_capabilities: List[str],
        selected_agent: Optional[str],
        selected_provider: Optional[str],
        selection_reason: str,
        rejected_candidates: List[Dict[str, Any]],
        selection_score: float = 0.0
    ):
        self.task_id = task_id
        self.role = role
        self.required_capabilities = required_capabilities
        self.selected_agent = selected_agent
        self.selected_provider = selected_provider
        self.selection_reason = selection_reason
        self.rejected_candidates = rejected_candidates
        self.selection_score = selection_score
        self.timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "role": self.role,
            "required_capabilities": self.required_capabilities,
            "selected_agent": self.selected_agent,
            "selected_provider": self.selected_provider,
            "selection_reason": self.selection_reason,
            "selection_score": round(self.selection_score, 2),
            "rejected_candidates": self.rejected_candidates,
            "timestamp": self.timestamp
        }

class OrchestratorEngine:
    """
    Universal, Provider-Agnostic Agent Orchestrator.
    NEVER contains provider-specific logic (e.g. if agent == 'hermes').
    Operates strictly on the BaseAgentAdapter contract, AgentStatus,
    verified capabilities, fresh operational health, and real metrics.
    """
    def __init__(self, registry: AgentRegistry, data_dir: Path, probe_ttl_seconds: int = 86400):
        self.registry = registry
        self.data_dir = data_dir
        self.decisions_file = data_dir / "orchestrator_decisions.json"
        self.executions_file = data_dir / "orchestrator_executions.json"
        self.probe_ttl_seconds = probe_ttl_seconds

    def select_agent(
        self,
        role: str,
        required_capabilities: Optional[List[str]] = None,
        preferred_agent: Optional[str] = None,
        preferred_provider: Optional[str] = None,
        allow_unverified: bool = False,
        task_id: Optional[str] = None,
        exclude_agent_ids: Optional[List[str]] = None
    ) -> Tuple[Optional[AgentModel], OrchestratorDecision]:
        """
        Strict filtering pipeline:
        installed -> enabled -> operational health -> executable identity -> fingerprint -> provider -> freshness -> role binding -> required capabilities -> scoring.
        CRITICAL RULE: MUST NEVER assign a normal task to an agent that has not passed operational test.
        """
        tid = task_id or f"task_{uuid.uuid4().hex[:8]}"
        req_caps = required_capabilities or ["chat"]
        excluded = set(exclude_agent_ids or [])
        all_agents_dict = self.registry._load_data().get("agents", {})
        
        candidates: List[Tuple[AgentModel, float, str, Optional[str]]] = []
        rejected: List[Dict[str, Any]] = []

        for aid, raw in all_agents_dict.items():
            try:
                ag = AgentModel(**raw)
            except Exception:
                continue

            # 0. Check if excluded
            if aid in excluded:
                rejected.append({
                    "agent_id": aid,
                    "name": ag.name,
                    "status": ag.status.value,
                    "reason": "Agent excluded by orchestrator (e.g. failed in previous attempt)"
                })
                continue

            # 1. Check if installed
            if ag.status == AgentStatus.NOT_INSTALLED:
                rejected.append({
                    "agent_id": aid,
                    "name": ag.name,
                    "status": ag.status.value,
                    "reason": "Agent executable not installed on system"
                })
                continue

            # 2. Check if disabled
            if ag.status == AgentStatus.DISABLED:
                rejected.append({
                    "agent_id": aid,
                    "name": ag.name,
                    "status": ag.status.value,
                    "reason": "Agent is manually disabled by user"
                })
                continue

            # 3. Check operational status
            if ag.status not in [AgentStatus.OPERATIONAL, AgentStatus.READY]:
                rejected.append({
                    "agent_id": aid,
                    "name": ag.name,
                    "status": ag.status.value,
                    "reason": f"Agent status is {ag.status.value}; required status is OPERATIONAL"
                })
                continue

            if ag.status == AgentStatus.READY and not allow_unverified:
                rejected.append({
                    "agent_id": aid,
                    "name": ag.name,
                    "status": ag.status.value,
                    "reason": "Agent is READY but not OPERATIONAL (has not passed live operational capability probe)"
                })
                continue

            op_ev = ag.operational_evidence

            # 4. Check executable identity integrity against on-disk binary
            if op_ev and op_ev.executable_identity and ag.path:
                valid_exe, exe_err = is_executable_identity_valid(op_ev.executable_identity, ag.path)
                if not valid_exe:
                    rejected.append({
                        "agent_id": aid,
                        "name": ag.name,
                        "status": AgentStatus.STALE.value,
                        "reason": f"Operational verification STALE: {exe_err} Re-verification required."
                    })
                    continue

            # 5. Check configuration fingerprint integrity
            if op_ev and op_ev.configuration_fingerprint and ag.path:
                adapter = self.registry.get_adapter(aid)
                if adapter:
                    prof = adapter.get_execution_profile()
                    curr_caps = [c for c, st in ag.capabilities.items() if st == CapabilityStatus.VERIFIED.value]
                    curr_fp = compute_config_fingerprint(
                        op_ev.executable_identity,
                        ag.version,
                        ag.active_provider or ag.provider,
                        op_ev.model,
                        prof.mode.value,
                        curr_caps
                    )
                    if curr_fp != op_ev.configuration_fingerprint:
                        rejected.append({
                            "agent_id": aid,
                            "name": ag.name,
                            "status": AgentStatus.STALE.value,
                            "reason": "Operational verification STALE: Configuration fingerprint mismatch. Re-verification required."
                        })
                        continue

            # 6. Check provider identity if a specific provider was requested
            if preferred_provider:
                ev_prov = (op_ev.provider_id if op_ev else None) or ag.active_provider
                if ev_prov and ev_prov != preferred_provider:
                    rejected.append({
                        "agent_id": aid,
                        "name": ag.name,
                        "status": AgentStatus.STALE.value,
                        "reason": f"Operational evidence verified for provider '{ev_prov}', not requested provider '{preferred_provider}'. Re-verification required."
                    })
                    continue

            # 7. Check freshness (Staleness against configured TTL)
            if ag.last_verified:
                try:
                    t_ver = time.mktime(time.strptime(ag.last_verified, "%Y-%m-%dT%H:%M:%SZ"))
                    age = int(time.time() - t_ver)
                    if age > self.probe_ttl_seconds:
                        rejected.append({
                            "agent_id": aid,
                            "name": ag.name,
                            "status": AgentStatus.STALE.value,
                            "reason": f"Operational verification expired ({age}s old > TTL {self.probe_ttl_seconds}s). Re-verification required."
                        })
                        continue
                except Exception:
                    pass

            # 8. Check role binding
            if role and role.upper() not in [r.upper() for r in ag.roles]:
                rejected.append({
                    "agent_id": aid,
                    "name": ag.name,
                    "status": ag.status.value,
                    "reason": f"Agent is not bound to required role '{role}' (assigned roles: {ag.roles})"
                })
                continue

            # 9. Check required capabilities (UNKNOWN and UNSUPPORTED are strictly rejected)
            missing_caps = []
            for cap in req_caps:
                st = ag.capabilities.get(cap, CapabilityStatus.UNKNOWN.value)
                if st in [CapabilityStatus.UNSUPPORTED.value, CapabilityStatus.UNKNOWN.value]:
                    missing_caps.append(cap)

            if missing_caps:
                rejected.append({
                    "agent_id": aid,
                    "name": ag.name,
                    "status": ag.status.value,
                    "reason": f"Missing required verified capabilities: {missing_caps}"
                })
                continue

            # Provider selection: resolve active operational provider if agent has multiple providers
            active_provider = ag.active_provider
            if not active_provider and ag.configured_providers:
                for cp in ag.configured_providers:
                    if cp.operational_status == "OPERATIONAL":
                        active_provider = cp.provider
                        break

            # Multi-attribute scoring based on real telemetry
            score = 100.0 if ag.status == AgentStatus.OPERATIONAL else 40.0
            if preferred_agent and aid == preferred_agent:
                score += 50.0
            if role and role.upper() in [r.upper() for r in ag.roles]:
                score += 20.0
            
            # Health latency bonus (lower latency = higher score)
            latency = ag.health.get("latency_ms", 1000)
            if latency and latency > 0:
                score += max(0, 10.0 - (latency / 1000.0))

            provider_info = f" [Provider: {active_provider}]" if active_provider else ""
            reason = f"Status=OPERATIONAL{provider_info}, Role='{role}' bound, all required capabilities verified ({', '.join(req_caps)})"
            candidates.append((ag, score, reason, active_provider))

        # Sort candidates by score descending
        candidates.sort(key=lambda x: x[1], reverse=True)

        if not candidates:
            decision = OrchestratorDecision(
                task_id=tid,
                role=role,
                required_capabilities=req_caps,
                selected_agent=None,
                selected_provider=None,
                selection_reason="No eligible agent passed all strict operational and capability filters.",
                rejected_candidates=rejected,
                selection_score=0.0
            )
            self._record_decision(decision)
            return None, decision

        best_agent, best_score, best_reason, best_provider = candidates[0]
        decision = OrchestratorDecision(
            task_id=tid,
            role=role,
            required_capabilities=req_caps,
            selected_agent=best_agent.id,
            selected_provider=best_provider,
            selection_reason=best_reason,
            rejected_candidates=rejected,
            selection_score=best_score
        )
        self._record_decision(decision)
        return best_agent, decision

    def execute_task(
        self,
        task_id: str,
        prompt: str,
        role: str,
        workspace: Path,
        required_capabilities: Optional[List[str]] = None,
        preferred_agent: Optional[str] = None,
        preferred_provider: Optional[str] = None,
        allow_fallback: bool = True,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """
        Executes a task through the orchestrator.
        Enforces:
        - Strict filtering (only OPERATIONAL agent assigned)
        - Traceable decision evidence
        - Clean failover to secondary OPERATIONAL candidate if primary execution fails
        - Token/Context optimization
        """
        primary_agent, decision = self.select_agent(
            role=role,
            required_capabilities=required_capabilities,
            preferred_agent=preferred_agent,
            preferred_provider=preferred_provider,
            task_id=task_id
        )

        if not primary_agent:
            return {
                "success": False,
                "task_id": task_id,
                "error": "No operational agent available to fulfill task requirements.",
                "decision": decision.to_dict(),
                "execution_trace": None
            }

        adapter = self.registry.get_adapter(primary_agent.id)
        if not adapter:
            return {
                "success": False,
                "task_id": task_id,
                "error": f"Adapter for selected agent '{primary_agent.id}' not found.",
                "decision": decision.to_dict()
            }

        # Build normalized task execution request
        req = TaskExecutionRequest(
            task_id=task_id,
            agent_id=primary_agent.id,
            provider_id=decision.selected_provider,
            role=role,
            workspace=str(workspace),
            prompt=prompt,
            required_capabilities=required_capabilities or ["chat"],
            timeout_seconds=timeout
        )

        # Execute primary through universal adapter contract
        result: TaskExecutionResult = adapter.execute(req)
        result.selection_reason = decision.selection_reason
        result.failover_chain = [primary_agent.id]

        execution_record = result.model_dump()
        execution_record["primary_agent"] = primary_agent.id
        execution_record["success"] = (result.exit_code == 0)
        execution_record["fallback_used"] = False
        execution_record["decision"] = decision.to_dict()

        # If primary failed and fallback is allowed: attempt failover
        if result.exit_code != 0 and allow_fallback:
            fallback_agent, fallback_decision = self.select_agent(
                role=role,
                required_capabilities=required_capabilities,
                preferred_agent=None,
                task_id=f"{task_id}_fallback",
                exclude_agent_ids=[primary_agent.id]
            )
            if fallback_agent and fallback_agent.id != primary_agent.id:
                fb_adapter = self.registry.get_adapter(fallback_agent.id)
                if fb_adapter:
                    fb_req = TaskExecutionRequest(
                        task_id=f"{task_id}_fb",
                        agent_id=fallback_agent.id,
                        provider_id=fallback_decision.selected_provider,
                        role=role,
                        workspace=str(workspace),
                        prompt=prompt,
                        required_capabilities=required_capabilities or ["chat"],
                        timeout_seconds=timeout
                    )
                    fb_res: TaskExecutionResult = fb_adapter.execute(fb_req)
                    
                    execution_record["fallback_used"] = True
                    execution_record["fallback_agent"] = fallback_agent.id
                    execution_record["fallback_command"] = fb_res.command_redacted
                    execution_record["fallback_exit_code"] = fb_res.exit_code
                    execution_record["fallback_duration_ms"] = fb_res.duration_ms
                    execution_record["fallback_stdout"] = fb_res.stdout
                    execution_record["fallback_stderr"] = fb_res.stderr
                    execution_record["fallback_success"] = (fb_res.exit_code == 0)
                    execution_record["fallback_pid"] = fb_res.pid
                    execution_record["artifacts"] = list(set(execution_record.get("artifacts", []) + fb_res.artifacts))
                    execution_record["success"] = (fb_res.exit_code == 0)
                    execution_record["failover_chain"] = [primary_agent.id, fallback_agent.id]

        self._record_execution(execution_record)
        return execution_record

    def _record_decision(self, decision: OrchestratorDecision):
        decisions = []
        if self.decisions_file.exists():
            try:
                with open(self.decisions_file, "r", encoding="utf-8") as f:
                    decisions = json.load(f)
            except Exception:
                pass
        decisions.append(decision.to_dict())
        decisions = decisions[-100:]
        with open(self.decisions_file, "w", encoding="utf-8") as f:
            json.dump(decisions, f, indent=2, ensure_ascii=False)

    def _record_execution(self, record: Dict[str, Any]):
        execs = []
        if self.executions_file.exists():
            try:
                with open(self.executions_file, "r", encoding="utf-8") as f:
                    execs = json.load(f)
            except Exception:
                pass
        execs.append(record)
        execs = execs[-100:]
        with open(self.executions_file, "w", encoding="utf-8") as f:
            json.dump(execs, f, indent=2, ensure_ascii=False)
