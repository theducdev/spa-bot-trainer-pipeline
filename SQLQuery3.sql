CREATE TABLE document_embeddings (
    [id] INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    [content] NVARCHAR(MAX) NULL,
    [embedding] NVARCHAR(MAX) NULL
);
