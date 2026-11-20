package com.syncspace.backend.repository;

import com.syncspace.backend.entity.Budget;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface BudgetRepository extends JpaRepository<Budget, Long>{
    List<Budget> findByWorkspaceId(Long workspaceId);
    Optional<Budget> findByWorkspaceIdAndCategoryAndMonthYear(Long workspaceId, String category, String monthYear);
}
