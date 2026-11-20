package com.syncspace.backend.dto;

import lombok.Data;

@Data
public class AddMemberRequest {
    private String email;
    private String role;
}
