package com.syncspace.backend.entity;

import com.syncspace.backend.enums.WorkspaceType;
import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "workspaces")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor

public class Workspace {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 100)
    private String name;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private WorkspaceType type;

    @Column(name = "is_finance_enabled")
    private Boolean isFinanceEnabled = true;

    @Column(name = "is_calender_enabled")
    private Boolean isCalenderEnabled = true;

    @Column(name = "is_todo_enabled")
    private Boolean isTodoEnabled = true;

    @Column(name = "created_at", insertable = false, updatable = false)
    private LocalDateTime createdAt;
}
