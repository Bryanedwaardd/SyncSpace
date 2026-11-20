package com.syncspace.backend.repository;

import com.syncspace.backend.entity.Schedule;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ScheduleRepository extends JpaRepository<Schedule, Long>{
    List<Schedule> findByWorkspaceId(Long workspaceId);
    List<Schedule> findByAssignedToId(Long userId);
}
