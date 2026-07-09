from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Dict, Iterable, List


class ProfileCleaner:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.profile_dir = project_root / "browser_profile"

    def clean_cache(self) -> Dict[str, Any]:
        if not self.profile_dir.exists():
            return {
                "ok": True,
                "message": "browser_profile does not exist yet.",
                "removed_bytes": 0,
                "removed_items": [],
                "errors": [],
            }

        removed_items: List[str] = []
        errors: List[str] = []
        removed_bytes = 0

        for path in self._targets():
            if not path.exists():
                continue
            try:
                size = self._path_size(path)
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
                removed_bytes += size
                removed_items.append(str(path.relative_to(self.profile_dir)))
            except Exception as exc:
                errors.append(f"{path.relative_to(self.profile_dir)}: {exc}")

        ok = not errors
        return {
            "ok": ok,
            "message": "Cache cleanup finished." if ok else "Cache cleanup finished with some locked files.",
            "removed_bytes": removed_bytes,
            "removed_items": removed_items,
            "errors": errors,
        }

    def clear_browser_history(self) -> Dict[str, Any]:
        if not self.profile_dir.exists():
            return {
                "ok": True,
                "message": "browser_profile does not exist yet.",
                "removed_bytes": 0,
                "removed_items": [],
                "errors": [],
            }

        removed_items: List[str] = []
        errors: List[str] = []
        removed_bytes = 0

        for path in self._history_targets():
            if not path.exists():
                continue
            try:
                size = self._path_size(path)
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
                removed_bytes += size
                removed_items.append(str(path.relative_to(self.profile_dir)))
            except Exception as exc:
                errors.append(f"{path.relative_to(self.profile_dir)}: {exc}")

        ok = not errors
        return {
            "ok": ok,
            "message": "Browser history cleared." if ok else "Browser history cleared with some locked files.",
            "removed_bytes": removed_bytes,
            "removed_items": removed_items,
            "errors": errors,
        }

    def _targets(self) -> Iterable[Path]:
        root_targets = [
            "Ad Blocking",
            "Autofill",
            "AutoLaunchProtocolsComponent",
            "BrowserMetrics",
            "CertificateRevocation",
            "component_crx_cache",
            "Crashpad",
            "Domain Actions",
            "EADPData Component",
            "Edge Data Protection Lists",
            "Edge Entity Extraction",
            "Edge Notifications",
            "Edge Shopping",
            "Edge Sidebar",
            "Edge Signal Triggers",
            "Edge Wallet",
            "Edge3pSerp",
            "EdgeArbitration",
            "EdgeLanguageDetectionModel",
            "extensions_crx_cache",
            "FirstPartySetsPreloaded",
            "GPUPersistentCache",
            "GrShaderCache",
            "hyphen-data",
            "MEIPreload",
            "Nurturing",
            "OnDeviceHeadSuggestModel",
            "OriginTrials",
            "PKIMetadata",
            "ProvenanceData",
            "ProvenanceDataAllowList",
            "ProvenanceDataTensors",
            "RecoveryImproved",
            "Safe Browsing",
            "SafetyTips",
            "ShaderCache",
            "SmartScreen",
            "Speech Recognition",
            "Subresource Filter",
            "Trust Protection Lists",
            "TrustTokenKeyCommitments",
            "Typosquatting",
            "Web Notifications Deny List",
            "Well Known Domains",
            "WidevineCdm",
            "WorkspacesNavigationComponent",
            "ZxcvbnData",
            "BrowserMetrics-spare.pma",
            "CrashpadMetrics-active.pma",
            "first_party_sets.db",
            "first_party_sets.db-journal",
            "Functional SAN Data",
            "Functional SAN Data-wal",
            "Variations",
            "en-US-10-1.bdic",
        ]

        default_targets = [
            "Cache",
            "Code Cache",
            "DawnCache",
            "DawnGraphiteCache",
            "DawnWebGPUCache",
            "EdgeCoupons",
            "Extension Rules",
            "Extension Scripts",
            "Extension State",
            "Extensions",
            "GPUCache",
            "GrShaderCache",
            "IndexedDB/blob_storage",
            "Local Extension Settings",
            "Service Worker/CacheStorage",
            "Service Worker/ScriptCache",
            "Shared Dictionary/cache",
            "ShaderCache",
            "Sync Data",
            "Sync Extension Settings",
        ]

        for item in root_targets:
            yield self.profile_dir / item
        for item in default_targets:
            yield self.profile_dir / "Default" / item

    def _history_targets(self) -> Iterable[Path]:
        root_targets = [
            "BrowserMetrics",
            "BrowserMetrics-spare.pma",
            "CrashpadMetrics-active.pma",
        ]

        default_targets = [
            "Affiliation Database",
            "Affiliation Database-journal",
            "BrowsingTopicsSiteData",
            "BrowsingTopicsSiteData-journal",
            "BrowsingTopicsState",
            "DashTrackerDatabase",
            "DashTrackerDatabase-journal",
            "DIPS",
            "DIPS-journal",
            "Download Service",
            "Favicons",
            "Favicons-journal",
            "heavy_ad_intervention_opt_out.db",
            "heavy_ad_intervention_opt_out.db-journal",
            "History",
            "History Provider Cache",
            "History-journal",
            "Network Action Predictor",
            "Network Action Predictor-journal",
            "Shortcuts",
            "Shortcuts-journal",
            "Top Sites",
            "Top Sites-journal",
            "Visited Links",
        ]

        for item in root_targets:
            yield self.profile_dir / item
        for item in default_targets:
            yield self.profile_dir / "Default" / item

    def _path_size(self, path: Path) -> int:
        if path.is_file():
            return path.stat().st_size
        total = 0
        for child in path.rglob("*"):
            try:
                if child.is_file():
                    total += child.stat().st_size
            except OSError:
                continue
        return total
