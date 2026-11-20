package com.syncspace.backend.dto;

import lombok.Data;

@Data
public class CreateWorkspaceRequest {
    private String name;
    private String type;
    private Long creatorId;
}
