import { Object, Property } from 'fabric-contract-api';

@Object()
export class Task {
    @Property()
    public docType?: string;

    @Property()
    public task_id!: string;

    @Property()
    public title!: string;

    @Property()
    public description!: string;

    @Property()
    public assignee!: string;

    @Property()
    public status!: string;

    @Property()
    public created_at!: string;

    @Property()
    public creator_identity!: string;

    @Property()
    public documents?: string[]; // Arrays of document IDs

    @Property()
    public approvals?: string[]; // Arrays of MSP IDs that approved closing
}

@Object()
export class DocumentVersion {
    @Property()
    public docType?: string;

    @Property()
    public document_id!: string;

    @Property()
    public version!: string;

    @Property()
    public content_hash!: string;

    @Property()
    public uploaded_at!: string;

    @Property()
    public uploaded_by!: string;

    @Property()
    public metadata?: string; // JSON string
}

