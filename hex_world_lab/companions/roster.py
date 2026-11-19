"""Companion relationship and command-state manager."""
from dataclasses import replace
from hex_world_lab.entities import EntityId, EntityKind, EntityRegistry
from .command import CompanionCommand
from .relationship import CompanionRelationship
class CompanionError(Exception): pass
class InvalidCompanionOwnerError(CompanionError,ValueError): pass
class InvalidCompanionEntityError(CompanionError,ValueError): pass
class CompanionAlreadyRecruitedError(CompanionError): pass
class UnknownCompanionError(CompanionError,LookupError): pass
class CompanionRoster:
    def __init__(self,registry:EntityRegistry)->None:
        if not isinstance(registry,EntityRegistry): raise TypeError("registry must be an EntityRegistry")
        self.registry=registry; self._by_npc:dict[EntityId,CompanionRelationship]={}
    def recruit(self,player_id:EntityId,npc_id:EntityId)->CompanionRelationship:
        player=self.registry.require(player_id); npc=self.registry.require(npc_id)
        if player.kind is not EntityKind.PLAYER: raise InvalidCompanionOwnerError("only PLAYER entities can own companions")
        if npc.kind is not EntityKind.NPC: raise InvalidCompanionEntityError("only NPC entities can be recruited")
        if not player.is_active or not npc.is_active: raise CompanionError("both entities must be active")
        if player.world_id!=npc.world_id or player.map_id!=npc.map_id: raise CompanionError("player and NPC must share world and map")
        if npc_id in self._by_npc: raise CompanionAlreadyRecruitedError(npc_id.value)
        relationship=CompanionRelationship(player_id,npc_id)
        self._by_npc[npc_id]=relationship; return relationship
    def dismiss(self,npc_id:EntityId)->CompanionRelationship:
        try:return self._by_npc.pop(npc_id)
        except KeyError:raise UnknownCompanionError(npc_id.value) from None
    def issue_command(self,npc_id:EntityId,command:CompanionCommand)->CompanionRelationship:
        if not isinstance(command,CompanionCommand): raise TypeError("command must be a CompanionCommand")
        try: old=self._by_npc[npc_id]
        except KeyError: raise UnknownCompanionError(npc_id.value) from None
        npc=self.registry.require(npc_id)
        wait=npc.transform.location.position if command is CompanionCommand.WAIT else None
        updated=replace(old,command=command,command_revision=old.command_revision+1,wait_position=wait)
        self._by_npc[npc_id]=updated; return updated
    def get_relationship(self,npc_id:EntityId)->CompanionRelationship|None:return self._by_npc.get(npc_id)
    def companions_for_player(self,player_id:EntityId)->tuple[CompanionRelationship,...]:
        return tuple(sorted((r for r in self._by_npc.values() if r.player_id==player_id),key=lambda r:r.companion_id.value))
    def remove_entity(self,entity_id:EntityId)->None:
        self._by_npc.pop(entity_id,None)
        for npc_id,relationship in tuple(self._by_npc.items()):
            if relationship.player_id==entity_id:self._by_npc.pop(npc_id)
    def all_relationships(self)->tuple[CompanionRelationship,...]:
        return tuple(sorted(self._by_npc.values(),key=lambda r:r.companion_id.value))
