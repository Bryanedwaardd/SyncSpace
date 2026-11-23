package com.syncspace.backend.service;

import com.syncspace.backend.entity.Transaction;
import com.syncspace.backend.entity.User;
import com.syncspace.backend.entity.Workspace;
import com.syncspace.backend.enums.TransactionType;
import com.syncspace.backend.repository.TransactionRepository;
import com.syncspace.backend.repository.UserRepository;
import com.syncspace.backend.repository.WorkspaceRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;

@Service
public class TransactionService {

    private final TransactionRepository transactionRepository;
    private final WorkspaceRepository workspaceRepository;
    private final UserRepository userRepository;
    private final MlClientService mlClientService;

    public TransactionService(TransactionRepository transactionRepository,
                              WorkspaceRepository workspaceRepository,
                              UserRepository userRepository,
                              MlClientService mlClientService) {
        this.transactionRepository = transactionRepository;
        this.workspaceRepository = workspaceRepository;
        this.userRepository = userRepository;
        this.mlClientService = mlClientService;
    }

    // Simpan transaksi langsung
    @Transactional
    public Transaction createTransaction(Transaction transaction) {
        return transactionRepository.save(transaction);
    }

    // 1. Proses Teks Chat -> FastAPI /parse
    @Transactional
    public Transaction processMlTextTransaction(Long workspaceId, Long userId, String rawText) {
        Map<String, Object> mlResult = mlClientService.parseText(rawText);
        return saveFromMlResult(workspaceId, userId, rawText, mlResult);
    }

    // 2. Proses Voice Note -> FastAPI /parse-voice
    @Transactional
    public Transaction processMlVoiceTransaction(Long workspaceId, Long userId, MultipartFile file) {
        Map<String, Object> mlResult = mlClientService.parseVoice(file);
        String transcript = (String) mlResult.getOrDefault("text", "Voice Note");
        return saveFromMlResult(workspaceId, userId, transcript, mlResult);
    }

    // 3. Proses Foto Struk -> FastAPI /parse-receipt
    @Transactional
    public Transaction processMlReceiptTransaction(Long workspaceId, Long userId, MultipartFile file) {
        Map<String, Object> mlResult = mlClientService.parseReceipt(file);
        String ocrText = (String) mlResult.getOrDefault("text", "Foto Struk");
        return saveFromMlResult(workspaceId, userId, ocrText, mlResult);
    }

    // Helper: Mapping hasil JSON Python FastAPI ke Entity Transaction
    private Transaction saveFromMlResult(Long workspaceId, Long userId, String rawText, Map<String, Object> mlResult) {
        Workspace workspace = workspaceRepository.findById(workspaceId)
                .orElseThrow(() -> new RuntimeException("Workspace tidak ditemukan dengan ID: " + workspaceId));
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new RuntimeException("User tidak ditemukan dengan ID: " + userId));

        Transaction transaction = new Transaction();
        transaction.setWorkspace(workspace);
        transaction.setUser(user);
        transaction.setRawText(rawText);

        // Mapping intent/type dari ML ("pengeluaran"/"EXPENSE" -> EXPENSE, "pemasukan"/"INCOME" -> INCOME)
        String rawIntent = String.valueOf(mlResult.getOrDefault("intent",
                mlResult.getOrDefault("type", "EXPENSE"))).toUpperCase();
        if (rawIntent.contains("INCOME") || rawIntent.contains("PEMASUKAN") || rawIntent.contains("MASUK")) {
            transaction.setType(TransactionType.INCOME);
        } else {
            transaction.setType(TransactionType.EXPENSE);
        }

        // Mapping kategori
        String category = (String) mlResult.getOrDefault("category", "General");
        transaction.setCategory(category != null ? category : "General");

        // Mapping nominal (mengecek key "amount" atau "total" dari FastAPI)
        Object amountObj = mlResult.get("amount") != null ? mlResult.get("amount") : mlResult.get("total");
        if (amountObj != null) {
            try {
                transaction.setAmount(new BigDecimal(amountObj.toString()));
            } catch (NumberFormatException e) {
                transaction.setAmount(BigDecimal.ZERO);
            }
        } else {
            transaction.setAmount(BigDecimal.ZERO);
        }

        // Deskripsi ringkas dari ML jika ada, fallback ke rawText
        String desc = (String) mlResult.getOrDefault("description", rawText);
        transaction.setDescription(desc != null ? desc : rawText);

        return transactionRepository.save(transaction);
    }

    public List<Transaction> getTransactionsByWorkspace(Long workspaceId) {
        return transactionRepository.findByWorkspaceId(workspaceId);
    }
}