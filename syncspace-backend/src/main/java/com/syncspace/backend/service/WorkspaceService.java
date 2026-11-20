package com.syncspace.backend.service;

import com.syncspace.backend.dto.CreateWorkspaceRequest;
import com.syncspace.backend.dto.WorkspaceResponse;
import com.syncspace.backend.dto.AddMemberRequest;
import com.syncspace.backend.entity.User;
import com.syncspace.backend.entity.Workspace;
import com.syncspace.backend.entity.WorkspaceMember;
import com.syncspace.backend.enums.Role;
import com.syncspace.backend.enums.WorkspaceType;
import com.syncspace.backend.repository.UserRepository;
import com.syncspace.backend.repository.WorkspaceMemberRepository;
import com.syncspace.backend.repository.WorkspaceRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class WorkspaceService {

    private final WorkspaceRepository workspaceRepository;
    private final WorkspaceMemberRepository workspaceMemberRepository;
    private final UserRepository userRepository;

    @Transactional
    public WorkspaceResponse createWorkspace(CreateWorkspaceRequest request) {
        User creator = userRepository.findById(request.getCreatorId())
                .orElseThrow(() -> new RuntimeException("User tidak ditemukan"));

        // 1. Simpan data workspace baru ke tabel workspaces
        Workspace workspace = new Workspace();
        workspace.setName(request.getName());
        workspace.setType(WorkspaceType.valueOf(request.getType().toUpperCase())); // "PERSONAL" atau "GROUP"
        Workspace savedWorkspace = workspaceRepository.save(workspace);

        // 2. Otomatis daftarkan pembuatnya sebagai ADMIN di workspace_members
        WorkspaceMember member = new WorkspaceMember();
        member.setWorkspace(savedWorkspace);
        member.setUser(creator);
        member.setRole(Role.ADMIN);
        workspaceMemberRepository.save(member);

        return new WorkspaceResponse(
                savedWorkspace.getId(),
                savedWorkspace.getName(),
                savedWorkspace.getType().name(),
                member.getRole().name()
        );
    }

    public List<WorkspaceResponse> getUserWorkspaces(Long userId) {
        List<WorkspaceMember> memberships = workspaceMemberRepository.findByUserId(userId);

        return memberships.stream()
                .map(m -> new WorkspaceResponse(
                        m.getWorkspace().getId(),
                        m.getWorkspace().getName(),
                        m.getWorkspace().getType().name(),
                        m.getRole().name()
                ))
                .collect(Collectors.toList());
    }

    @Transactional
    public WorkspaceResponse addMember(Long workspaceId, AddMemberRequest request){
        Workspace workspace = workspaceRepository.findById(workspaceId)
                .orElseThrow(() -> new RuntimeException("Workspace tidak ditemukan"));
        if (workspace.getType() == WorkspaceType.PERSONAL){
            throw new RuntimeException("Tidak dapat menambahkan anggota ke Personal Workspace");
        }

        User userToAdd = userRepository.findByEmail(request.getEmail())
                .orElseThrow(() -> new RuntimeException("User dengan email tersebut tidak ditemukan"));

        if(workspaceMemberRepository.findByWorkspaceIdAndUserId(workspaceId, userToAdd.getId()).isPresent()){
            throw new RuntimeException("User sudah tergabung di workspace ini");
        }

        Role assignedRole = (request.getRole() != null)
                ?Role.valueOf(request.getRole().toUpperCase())
                :Role.MEMBER;

        WorkspaceMember newMember = new WorkspaceMember();
        newMember.setWorkspace(workspace);
        newMember.setUser(userToAdd);
        newMember.setRole(assignedRole);
        workspaceMemberRepository.save(newMember);

        return new WorkspaceResponse(
                workspace.getId(),
                workspace.getName(),
                workspace.getType().name(),
                newMember.getRole().name()
        );
    }
}