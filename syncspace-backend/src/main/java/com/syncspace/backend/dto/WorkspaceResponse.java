package com.syncspace.backend.dto;

import lombok.Data;
import lombok.AllArgsConstructor;

@Data
@AllArgsConstructor
public class WorkspaceResponse {
    private Long id;
    private String name;
    private String type;
    private String role;
}
