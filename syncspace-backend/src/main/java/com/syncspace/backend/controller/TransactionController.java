package com.syncspace.backend.controller;

import com.syncspace.backend.entity.Transaction;
import com.syncspace.backend.service.TransactionService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

@RestController
@RequestMapping("/api/v1/transactions")
public class TransactionController {

    private final TransactionService transactionService;

    public TransactionController(TransactionService transactionService) {
        this.transactionService = transactionService;
    }

    // 1. Input transaksi manual
    @PostMapping
    public ResponseEntity<Transaction> createTransaction(@RequestBody Transaction transaction) {
        return new ResponseEntity<>(transactionService.createTransaction(transaction), HttpStatus.CREATED);
    }

    // 2. Input teks chat -> ML FastAPI (/parse)
    @PostMapping("/parse-text")
    public ResponseEntity<Transaction> parseText(
            @RequestParam Long workspaceId,
            @RequestParam Long userId,
            @RequestBody String rawText) {
        Transaction saved = transactionService.processMlTextTransaction(workspaceId, userId, rawText);
        return new ResponseEntity<>(saved, HttpStatus.CREATED);
    }

    // 3. Input voice note -> ML FastAPI (/parse-voice)
    @PostMapping("/parse-voice")
    public ResponseEntity<Transaction> parseVoice(
            @RequestParam Long workspaceId,
            @RequestParam Long userId,
            @RequestParam("file") MultipartFile file) {
        Transaction saved = transactionService.processMlVoiceTransaction(workspaceId, userId, file);
        return new ResponseEntity<>(saved, HttpStatus.CREATED);
    }

    // 4. Input foto struk -> ML FastAPI (/parse-receipt)
    @PostMapping("/parse-image")
    public ResponseEntity<Transaction> parseReceipt(
            @RequestParam Long workspaceId,
            @RequestParam Long userId,
            @RequestParam("file") MultipartFile file) {
        Transaction saved = transactionService.processMlReceiptTransaction(workspaceId, userId, file);
        return new ResponseEntity<>(saved, HttpStatus.CREATED);
    }

    // 5. Ambil semua transaksi per workspace
    @GetMapping("/workspace/{workspaceId}")
    public ResponseEntity<List<Transaction>> getByWorkspace(@PathVariable Long workspaceId) {
        return ResponseEntity.ok(transactionService.getTransactionsByWorkspace(workspaceId));
    }
}