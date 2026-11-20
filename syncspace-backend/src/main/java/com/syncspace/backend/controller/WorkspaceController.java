package com.syncspace.backend.controller;

import com.syncspace.backend.dto.AddMemberRequest;
import com.syncspace.backend.dto.CreateWorkspaceRequest;
import com.syncspace.backend.dto.WorkspaceResponse;
import com.syncspace.backend.service.WorkspaceService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("api/v1/workspaces")
@RequiredArgsConstructor
public class WorkspaceController {

    private final WorkspaceService workspaceService;

    //1. Membuat Workspace baru (PERSONAL atau GROUP)
    @PostMapping
    public ResponseEntity<WorkspaceResponse> createWorkspace(@RequestBody CreateWorkspaceRequest request){
        WorkspaceResponse response = workspaceService.createWorkspace(request);
        return new ResponseEntity<>(response, HttpStatus.CREATED);
    }

    //2. Mengambil daftar semua Workspace milik user tertentu
    @GetMapping("/user/{userId}")
    public ResponseEntity<List<WorkspaceResponse>> getUserWorkspaces(@PathVariable Long userId){
        List<WorkspaceResponse> workspaces = workspaceService.getUserWorkspaces(userId);
        return ResponseEntity.ok(workspaces);
    }

    //3. Menambahkan anggota baru ke dalam Group Workspace
    @PostMapping("/{workspaceId}/members")
    public ResponseEntity<WorkspaceResponse> addMember(
            @PathVariable Long workspaceId,
            @RequestBody AddMemberRequest request) {
        WorkspaceResponse response = workspaceService.addMember(workspaceId, request);
        return new ResponseEntity<>(response, HttpStatus.CREATED);
    }
}
