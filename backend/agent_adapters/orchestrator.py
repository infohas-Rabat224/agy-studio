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
        selection_score: float = 0.0,
        session_id: Optional[str] = None
    ):
        self.task_id = task_id
        self.role = role
        self.required_capabilities = required_capabilities
        self.selected_agent = selected_agent
        self.selected_provider = selected_provider
        self.selection_reason = selection_reason
        self.rejected_candidates = rejected_candidates
        self.selection_score = selection_score
        self.session_id = session_id
        self.timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def to_dict(self) -> Dict[str, Any]:
        d = {
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
        if self.session_id:
            d["session_id"] = self.session_id
        return d

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
                st = (
                    ag.capabilities.get(cap) or
                    ag.capabilities.get(cap.upper()) or
                    ag.capabilities.get(cap.lower(), CapabilityStatus.UNKNOWN.value)
                )
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
        timeout: int = 60,
        artifacts: Optional[List[Dict[str, Any]]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes a task through the orchestrator.
        Enforces:
        - Workspace existence validation
        - Strict filtering (only OPERATIONAL agent assigned)
        - Traceable decision evidence
        - Multimodal artifact context handoff
        - Session correlation
        - Clean failover to secondary OPERATIONAL candidate if primary execution fails
        - Token/Context optimization
        """
        ws = Path(workspace)
        if not ws.exists() or not ws.is_dir():
            return {
                "success": False,
                "task_id": task_id,
                "error": f"Workspace introuvable ou inaccessible : {workspace}",
                "decision": None,
                "execution_trace": None
            }

        # Normalize artifacts and check if task or artifacts require IMAGE_VISION
        requires_image_vision = False
        primary_artifact_id = None
        artifact_dicts: List[Dict[str, Any]] = []

        if artifacts:
            for art in artifacts:
                if hasattr(art, "model_dump"):
                    ad = art.model_dump()
                elif hasattr(art, "to_summary_dict"):
                    ad = art.to_summary_dict()
                elif isinstance(art, dict):
                    ad = dict(art)
                else:
                    ad = {"name": str(art), "type": "unknown"}
                artifact_dicts.append(ad)

                aid = ad.get("id") or ad.get("artifact_id")
                if not primary_artifact_id and aid:
                    primary_artifact_id = aid

                atype = str(ad.get("source_type") or ad.get("type") or "").upper()
                ext = str(ad.get("extension") or os.path.splitext(ad.get("name", ""))[1]).lower()
                has_extracted_text = bool(
                    ad.get("extracted_text") or
                    (ad.get("content") and isinstance(ad.get("content"), dict) and ad.get("content").get("extracted_text"))
                )

                is_image = atype in ("IMAGE", "SCREENSHOT", "CLIPBOARD_IMAGE") or ext in (".png", ".jpg", ".jpeg", ".webp", ".bmp")
                if is_image and not has_extracted_text:
                    requires_image_vision = True

        if required_capabilities and any(c.upper() in ("IMAGE_VISION", "VISION") for c in required_capabilities):
            requires_image_vision = True

        if requires_image_vision:
            vision_candidates = self.registry.agents_with_verified_capability("IMAGE_VISION")
            if not vision_candidates:
                # Per Anti-Fabrication Rule: Strictly REFUSE sending image to text-only agents
                # Record forensic correlation chain
                try:
                    from ..session.session_manager import SessionManager
                    sm = SessionManager.get_instance(self.data_dir)
                    sm.record_correlation(
                        task_id=task_id,
                        session_id=session_id,
                        artifact_id=primary_artifact_id,
                        artifact_ids=[primary_artifact_id] if primary_artifact_id else [],
                        execution_id=None,
                        agent_id=None,
                        provider_id=None,
                        capabilities=["IMAGE_INGESTION"],
                        result="VISION_AGENT_UNAVAILABLE",
                        reason="BLOCKED — NO OPERATIONAL VISION-CAPABLE AGENT",
                        details="Task requires IMAGE_VISION, but host has no operational vision-capable agent. Refusing to send raw image to text-only agent."
                    )
                except Exception:
                    pass

                return {
                    "success": False,
                    "task_id": task_id,
                    "status": "VISION_AGENT_UNAVAILABLE",
                    "result": "VISION_AGENT_UNAVAILABLE",
                    "primary_agent": None,
                    "exit_code": 1,
                    "error": "VISION_AGENT_UNAVAILABLE: No operational agent has verified IMAGE_VISION capability.",
                    "reason": "BLOCKED — NO OPERATIONAL VISION-CAPABLE AGENT",
                    "decision": None,
                    "execution_trace": None,
                    "correlation_chain": {
                        "session_id": session_id or "default",
                        "artifact_id": primary_artifact_id,
                        "task_id": task_id,
                        "result": "VISION_AGENT_UNAVAILABLE",
                        "reason": "BLOCKED — NO OPERATIONAL VISION-CAPABLE AGENT"
                    }
                }
            else:
                # Add IMAGE_VISION to required capabilities
                req_caps_list = list(required_capabilities or ["chat"])
                if not any(c.upper() in ("IMAGE_VISION", "VISION") for c in req_caps_list):
                    req_caps_list.append("IMAGE_VISION")
                required_capabilities = req_caps_list

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

        # Build prompt with normalized artifact context if artifacts supplied
        effective_prompt = prompt
        if artifact_dicts:
            art_contexts = []
            for art in artifact_dicts:
                aname = art.get("name", "artifact")
                atype = art.get("source_type") or art.get("type", "document")
                ext_txt = art.get("extracted_text") or art.get("text")
                if not ext_txt and isinstance(art.get("content"), dict):
                    ext_txt = art.get("content", {}).get("extracted_text") or art.get("content", {}).get("text")
                if ext_txt:
                    art_contexts.append(f"--- [Artifact: {aname} ({atype})] ---\n{ext_txt}")
                else:
                    path_val = art.get("path") or (art.get("content", {}).get("binary_path") if isinstance(art.get("content"), dict) else None)
                    art_contexts.append(f"--- [Artifact: {aname} ({atype})] --- (File: {path_val})")
            if art_contexts:
                effective_prompt = f"{prompt}\n\n=== ATTACHED ARTIFACTS CONTEXT ===\n" + "\n\n".join(art_contexts)

        # Build normalized task execution request
        req = TaskExecutionRequest(
            task_id=task_id,
            agent_id=primary_agent.id,
            provider_id=decision.selected_provider,
            role=role,
            workspace=str(workspace),
            prompt=effective_prompt,
            required_capabilities=required_capabilities or ["chat"],
            timeout_seconds=timeout,
            session_id=session_id,
            artifacts=artifacts or []
        )

        # Execute primary through universal adapter contract
        result: TaskExecutionResult = adapter.execute(req)
        result.selection_reason = decision.selection_reason
        result.failover_chain = [primary_agent.id]
        if session_id:
            result.session_id = session_id

        execution_record = result.model_dump()
        execution_record["primary_agent"] = primary_agent.id
        execution_record["success"] = (result.exit_code == 0)
        execution_record["fallback_used"] = False
        execution_record["decision"] = decision.to_dict()
        execution_record["session_id"] = session_id
        execution_record["input_artifacts"] = artifacts or []

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
                        prompt=effective_prompt,
                        required_capabilities=required_capabilities or ["chat"],
                        timeout_seconds=timeout,
                        session_id=session_id,
                        artifacts=artifacts or []
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

        # Attach execution to session if available
        try:
            from ..session.session_manager import SessionManager
            sm = SessionManager.get_instance(self.data_dir)
            curr = sm.get_current_session()
            if curr and (session_id is None or curr.session_id == session_id):
                sm.attach_execution(
                    execution_id=result.execution_id,
                    task_id=task_id,
                    agent_id=primary_agent.id,
                    workspace=str(workspace),
                    status=result.status,
                    started_at=result.started_at,
                    ended_at=result.ended_at,
                    duration_ms=result.duration_ms,
                    exit_code=result.exit_code,
                    artifacts=result.artifacts
                )
                # Record complete Session → Artifact → Task → Agent → Execution correlation chain
                art_ids = [
                    a.get("id") or a.get("artifact_id") for a in artifact_dicts
                    if a.get("id") or a.get("artifact_id")
                ]
                primary_art = primary_artifact_id or (art_ids[0] if art_ids else None)
                executed_agent = execution_record.get("fallback_agent") if execution_record.get("fallback_used") else primary_agent.id
                corr_res = "COMPLETED" if execution_record.get("success") else "FAILED"
                sm.record_correlation(
                    task_id=task_id,
                    session_id=session_id,
                    artifact_id=primary_art,
                    artifact_ids=art_ids,
                    execution_id=execution_record.get("execution_id"),
                    agent_id=executed_agent,
                    provider_id=decision.selected_provider if decision else None,
                    capabilities=decision.required_capabilities if decision else (required_capabilities or []),
                    result=corr_res,
                    reason=decision.selection_reason if decision else None,
                    details=f"Execution completed in {execution_record.get('duration_ms', 0)}ms (Exit {execution_record.get('exit_code')})"
                )
        except Exception:
            pass

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
